"""
Módulo que implementa o cliente para a API da Suna Core.

Este módulo fornece uma interface para comunicação com a Suna Core,
permitindo a execução de agentes, consulta de status e outras operações.
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.utils.retry import async_retry

# Configurar logger
logger = logging.getLogger(__name__)

class SunaClient:
    """Cliente para a API da Suna Core."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o cliente Suna."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o cliente Suna."""
        self.api_url = settings.SUNA_API_URL
        if not self.api_url:
            raise ValueError("SUNA_API_URL não configurada")
        
        self.api_key = settings.SUNA_API_KEY
        if not self.api_key:
            raise ValueError("SUNA_API_KEY não configurada")
        
        # Remover barra final da URL se presente
        if self.api_url.endswith("/"):
            self.api_url = self.api_url[:-1]
        
        # Configurações de timeout e retry
        self.timeout = 30.0  # segundos
        self.max_retries = 3
        
        logger.info(f"Cliente Suna inicializado com URL: {self.api_url}")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição para a API da Suna.
        
        Args:
            method: Método HTTP (GET, POST, etc.).
            endpoint: Endpoint da API.
            data: Dados a serem enviados no corpo da requisição.
            params: Parâmetros de query string.
            headers: Cabeçalhos HTTP adicionais.
            
        Returns:
            Resposta da API.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        url = f"{self.api_url}{endpoint}"
        
        # Preparar headers
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            request_headers.update(headers)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, params=params, headers=request_headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, params=params, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=request_headers)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP na requisição para {url}: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
            except:
                error_message = str(e)
            
            raise Exception(f"Erro na API da Suna: {error_message}")
        except httpx.RequestError as e:
            logger.error(f"Erro na requisição para {url}: {str(e)}")
            raise Exception(f"Erro de conexão com a API da Suna: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado na requisição para {url}: {str(e)}")
            raise
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def execute_agent(
        self,
        prompt: str,
        agent_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa um agente na Suna Core.
        
        Args:
            prompt: Prompt para o agente.
            agent_config: Configuração do agente.
            context: Contexto adicional para o agente.
            metadata: Metadados adicionais.
            
        Returns:
            Resultado da execução.
            
        Raises:
            Exception: Se ocorrer um erro na execução.
        """
        endpoint = "/api/agent/execute"
        
        # Preparar dados da requisição
        data = {
            "prompt": prompt,
            "config": agent_config
        }
        
        if context:
            data["context"] = context
        
        if metadata:
            data["metadata"] = metadata
        
        logger.info(f"Executando agente na Suna Core: {json.dumps(data)[:100]}...")
        
        return await self._make_request("POST", endpoint, data=data)
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def get_execution_status(self, execution_id: Union[str, UUID]) -> Dict[str, Any]:
        """Obtém o status de uma execução.
        
        Args:
            execution_id: ID da execução.
            
        Returns:
            Status da execução.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        endpoint = f"/api/agent/status/{execution_id}"
        
        logger.info(f"Obtendo status da execução {execution_id} na Suna Core...")
        
        return await self._make_request("GET", endpoint)
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def cancel_execution(self, execution_id: Union[str, UUID]) -> Dict[str, Any]:
        """Cancela uma execução em andamento.
        
        Args:
            execution_id: ID da execução.
            
        Returns:
            Resultado da operação.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        endpoint = f"/api/agent/cancel/{execution_id}"
        
        logger.info(f"Cancelando execução {execution_id} na Suna Core...")
        
        return await self._make_request("POST", endpoint)
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Obtém a lista de ferramentas disponíveis na Suna Core.
        
        Returns:
            Lista de ferramentas disponíveis.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        endpoint = "/api/tools"
        
        logger.info("Obtendo lista de ferramentas disponíveis na Suna Core...")
        
        response = await self._make_request("GET", endpoint)
        return response.get("tools", [])
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Obtém a lista de modelos disponíveis na Suna Core.
        
        Returns:
            Lista de modelos disponíveis.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        endpoint = "/api/models"
        
        logger.info("Obtendo lista de modelos disponíveis na Suna Core...")
        
        response = await self._make_request("GET", endpoint)
        return response.get("models", [])
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def health_check(self) -> bool:
        """Verifica se a API da Suna Core está disponível.
        
        Returns:
            True se a API está disponível, False caso contrário.
        """
        endpoint = "/api/health"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response.get("status") == "ok"
        except Exception as e:
            logger.error(f"Erro no health check da Suna Core: {str(e)}")
            return False


# Instância global do cliente Suna
suna_client = SunaClient.get_instance()