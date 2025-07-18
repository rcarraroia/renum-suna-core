"""
Utilitário para implementar mecanismos de retry em operações que podem falhar temporariamente.

Este módulo fornece decoradores e funções para implementar retry em operações
que podem falhar devido a problemas temporários de rede ou serviço.
"""

import time
import logging
import functools
from typing import Callable, Any, List, Optional, Type, Union

# Configurar logger
logger = logging.getLogger(__name__)

def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
):
    """Decorador para implementar retry em funções que podem falhar temporariamente.
    
    Args:
        max_retries: Número máximo de tentativas.
        delay: Tempo de espera inicial entre tentativas (em segundos).
        backoff_factor: Fator de multiplicação do tempo de espera a cada tentativa.
        exceptions: Exceções que devem ser capturadas para retry.
    
    Returns:
        Decorador configurado.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"Tentativa {attempt} de {max_retries} para {func.__name__}")
                    
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Tentativa {attempt + 1}/{max_retries} falhou para {func.__name__}: {str(e)}. "
                            f"Tentando novamente em {current_delay:.2f} segundos..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Todas as {max_retries} tentativas falharam para {func.__name__}: {str(e)}"
                        )
            
            # Se chegou aqui, todas as tentativas falharam
            raise last_exception
        
        return wrapper
    
    return decorator


async def async_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    **kwargs
) -> Any:
    """Função para implementar retry em funções assíncronas que podem falhar temporariamente.
    
    Args:
        func: Função assíncrona a ser executada.
        *args: Argumentos posicionais para a função.
        max_retries: Número máximo de tentativas.
        delay: Tempo de espera inicial entre tentativas (em segundos).
        backoff_factor: Fator de multiplicação do tempo de espera a cada tentativa.
        exceptions: Exceções que devem ser capturadas para retry.
        **kwargs: Argumentos nomeados para a função.
    
    Returns:
        Resultado da função.
    
    Raises:
        Exception: Se todas as tentativas falharem.
    """
    import asyncio
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(f"Tentativa {attempt} de {max_retries} para {func.__name__}")
            
            return await func(*args, **kwargs)
        
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(
                    f"Tentativa {attempt + 1}/{max_retries} falhou para {func.__name__}: {str(e)}. "
                    f"Tentando novamente em {current_delay:.2f} segundos..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(
                    f"Todas as {max_retries} tentativas falharam para {func.__name__}: {str(e)}"
                )
    
    # Se chegou aqui, todas as tentativas falharam
    raise last_exception