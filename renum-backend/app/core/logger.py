"""
Configuração de logging para a aplicação.

Este módulo configura o sistema de logging para a aplicação,
incluindo formatação, níveis de log e handlers.
"""

import logging
import sys
from typing import Dict, Any

from app.core.config import get_settings


class RequestIdFilter(logging.Filter):
    """Filtro para adicionar o ID da requisição aos logs."""
    
    def __init__(self, request_id: str = None):
        super().__init__()
        self.request_id = request_id
    
    def filter(self, record):
        record.request_id = getattr(record, "request_id", self.request_id or "-")
        return True


def setup_logging():
    """
    Configura o sistema de logging.
    
    Returns:
        Logger configurado
    """
    settings = get_settings()
    
    # Configura o nível de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configura o formato do log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configura o handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Adiciona o filtro para request_id
    handler.addFilter(RequestIdFilter())
    
    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Configura o logger da aplicação
    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    
    # Reduz o nível de log de bibliotecas externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    return logger


# Cria o logger global
logger = setup_logging()


def get_logger(name: str):
    """
    Obtém um logger com o nome especificado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_with_context(logger, level: str, message: str, context: Dict[str, Any] = None):
    """
    Registra uma mensagem de log com contexto adicional.
    
    Args:
        logger: Logger a ser utilizado
        level: Nível de log (debug, info, warning, error, critical)
        message: Mensagem de log
        context: Contexto adicional para o log
    """
    log_method = getattr(logger, level.lower())
    
    if context:
        # Adiciona o contexto como atributos extras
        extra = {k: v for k, v in context.items()}
        log_method(message, extra=extra)
    else:
        log_method(message)