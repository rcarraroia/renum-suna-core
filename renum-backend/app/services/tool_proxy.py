"""
Módulo que implementa o proxy para ferramentas externas.

Este módulo fornece uma interface para proxying de chamadas de ferramentas
da Suna Core para APIs externas, usando as credenciais do cliente.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.retry import async_retry
from app.services.credentials import credential_service

# Configurar logger
logger = logging.getLogger(__name__)

class ToolProxy:
    """Proxy para ferramentas externas."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o proxy de ferramentas."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o proxy de ferramentas."""
        # Configurações de timeout e retry
        self.timeout = 30.0  # segundos
        self.max_retries = 3
        
        # Mapeamento de ferramentas suportadas
        self.supported_tools = {
            "tavily_search": {
                "base_url": "https://api.tavily.com",
                "endpoints": {
                    "search": "/v1/search"
                },
                "credential_key": "TAVILY_API_KEY",
                "auth_header": "x-api-key"
            },
            "firecrawl": {
                "base_url": "https://api.firecrawl.dev",
                "endpoints": {
                    "crawl": "/v1/crawl",
                    "extract": "/v1/extract"
                },
                "credential_key": "FIRECRAWL_API_KEY",
                "auth_header": "x-api-key"
            },
            # Adicionar mais ferramentas conforme necessário
        }
        
        logger.info("Proxy de ferramentas inicializado")
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição para uma API externa.
        
        Args:
            method: Método HTTP (GET, POST, etc.).
            url: URL da API.
            data: Dados a serem enviados no corpo da requisição.
            params: Parâmetros de query string.
            headers: Cabeçalhos HTTP adicionais.
            
        Returns:
            Resposta da API.
            
        Raises:
            Exception: Se ocorrer um erro na requisição.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, params=params, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, params=params, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=headers)
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
            
            raise Exception(f"Erro na API externa: {error_message}")
        except httpx.RequestError as e:
            logger.error(f"Erro na requisição para {url}: {str(e)}")
            raise Exception(f"Erro de conexão com a API externa: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado na requisição para {url}: {str(e)}")
            raise
    
    @async_retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    async def proxy_tool_call(
        self,
        client_id: Union[str, UUID],
        tool_name: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Faz proxy de uma chamada de ferramenta.
        
        Args:
            client_id: ID do cliente.
            tool_name: Nome da ferramenta.
            action: Ação a ser executada.
            parameters: Parâmetros da ação.
            
        Returns:
            Resultado da chamada.
            
        Raises:
            ValueError: Se a ferramenta ou ação não for suportada.
            Exception: Se ocorrer um erro na chamada.
        """
        # Verificar se a ferramenta é suportada
        if tool_name not in self.supported_tools:
            raise ValueError(f"Ferramenta não suportada: {tool_name}")
        
        tool_config = self.supported_tools[tool_name]
        
        # Verificar se a ação é suportada
        if action not in tool_config["endpoints"]:
            raise ValueError(f"Ação não suportada para {tool_name}: {action}")
        
        # Obter credencial do cliente
        credential_key = tool_config["credential_key"]
        credential = await credential_service.get_credential(client_id, credential_key)
        
        if not credential:
            raise ValueError(f"Credencial {credential_key} não encontrada para o cliente {client_id}")
        
        # Construir URL
        base_url = tool_config["base_url"]
        endpoint = tool_config["endpoints"][action]
        url = f"{base_url}{endpoint}"
        
        # Preparar headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Adicionar header de autenticação
        auth_header = tool_config["auth_header"]
        headers[auth_header] = credential
        
        # Fazer requisição
        logger.info(f"Fazendo proxy de chamada para {tool_name}.{action}: {json.dumps(parameters)[:100]}...")
        
        # Registrar uso da ferramenta (para faturamento)
        # TODO: Implementar rastreamento de uso
        
        return await self._make_request("POST", url, data=parameters, headers=headers)
    
    async def is_tool_available(self, client_id: Union[str, UUID], tool_name: str) -> bool:
        """Verifica se uma ferramenta está disponível para um cliente.
        
        Args:
            client_id: ID do cliente.
            tool_name: Nome da ferramenta.
            
        Returns:
            True se a ferramenta está disponível, False caso contrário.
        """
        # Verificar se a ferramenta é suportada
        if tool_name not in self.supported_tools:
            return False
        
        # Verificar se o cliente tem a credencial necessária
        tool_config = self.supported_tools[tool_name]
        credential_key = tool_config["credential_key"]
        
        credential = await credential_service.get_credential(client_id, credential_key)
        return credential is not None
    
    async def get_available_tools(self, client_id: Union[str, UUID]) -> List[str]:
        """Obtém a lista de ferramentas disponíveis para um cliente.
        
        Args:
            client_id: ID do cliente.
            
        Returns:
            Lista de nomes de ferramentas disponíveis.
        """
        available_tools = []
        
        for tool_name in self.supported_tools:
            if await self.is_tool_available(client_id, tool_name):
                available_tools.append(tool_name)
        
        return available_tools


# Instância global do proxy de ferramentas
tool_proxy = ToolProxy.get_instance()