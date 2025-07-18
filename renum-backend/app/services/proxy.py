"""
Módulo que implementa o serviço de proxy para ferramentas externas na Plataforma Renum.

Este módulo fornece funcionalidades para encaminhar requisições para serviços externos,
utilizando as credenciais dos clientes de forma segura e rastreando o uso para fins de faturamento.
"""

import logging
import json
import time
import httpx
from typing import Dict, Any, Optional, Union, List
from uuid import UUID

from app.services.credentials import credential_service
from app.services.usage_tracking import usage_tracking_service
from app.core.config import settings

# Configurar logger
logger = logging.getLogger(__name__)

class ProxyService:
    """Serviço de proxy para ferramentas externas."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de proxy."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de proxy."""
        self.timeout = 60.0  # Timeout padrão para requisições (em segundos)
        self.supported_services = {
            "tavily": {
                "base_url": "https://api.tavily.com",
                "endpoints": {
                    "search": "/v1/search",
                    "images": "/v1/images"
                }
            },
            "firecrawl": {
                "base_url": "https://api.firecrawl.dev",
                "endpoints": {
                    "crawl": "/v1/crawl",
                    "extract": "/v1/extract"
                }
            }
        }
        logger.info("Serviço de proxy inicializado")
    
    async def _get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Obtém a configuração de um serviço.
        
        Args:
            service_name: Nome do serviço.
            
        Returns:
            Configuração do serviço.
            
        Raises:
            ValueError: Se o serviço não for suportado.
        """
        service_config = self.supported_services.get(service_name.lower())
        if not service_config:
            raise ValueError(f"Serviço não suportado: {service_name}")
        return service_config
    
    async def _get_credential(self, service_name: str, client_id: Union[str, UUID]) -> str:
        """Obtém a credencial de um cliente para um serviço.
        
        Args:
            service_name: Nome do serviço.
            client_id: ID do cliente.
            
        Returns:
            Credencial do cliente para o serviço.
            
        Raises:
            ValueError: Se a credencial não for encontrada.
        """
        credential = await credential_service.get_active_credential_for_service(service_name, client_id)
        if not credential or not hasattr(credential, "decrypted_data"):
            raise ValueError(f"Credencial não encontrada para o serviço {service_name}")
        
        # A maioria dos serviços usa 'api_key' como chave para a credencial
        return credential.decrypted_data.get("api_key")
    
    async def _track_usage(
        self, 
        service_name: str, 
        endpoint: str, 
        client_id: Union[str, UUID], 
        user_id: Optional[Union[str, UUID]], 
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        execution_time: float,
        status_code: int,
        error: Optional[str] = None
    ) -> None:
        """Rastreia o uso de um serviço externo.
        
        Args:
            service_name: Nome do serviço.
            endpoint: Endpoint do serviço.
            client_id: ID do cliente.
            user_id: ID do usuário.
            request_data: Dados da requisição.
            response_data: Dados da resposta.
            execution_time: Tempo de execução da requisição (em segundos).
            status_code: Código de status HTTP da resposta.
            error: Mensagem de erro, se houver.
        """
        try:
            # Remover dados sensíveis antes de registrar
            sanitized_request = self._sanitize_data(request_data)
            sanitized_response = self._sanitize_data(response_data)
            
            # Registrar uso
            await usage_tracking_service.track_external_service_usage(
                service_name=service_name,
                endpoint=endpoint,
                client_id=client_id,
                user_id=user_id,
                request_data=sanitized_request,
                response_data=sanitized_response,
                execution_time=execution_time,
                status_code=status_code,
                error=error
            )
        except Exception as e:
            logger.error(f"Erro ao rastrear uso do serviço {service_name}: {str(e)}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove dados sensíveis de um dicionário.
        
        Args:
            data: Dicionário a ser sanitizado.
            
        Returns:
            Dicionário sanitizado.
        """
        if not data:
            return {}
        
        # Criar uma cópia para não modificar o original
        sanitized = data.copy()
        
        # Lista de chaves sensíveis a serem removidas ou mascaradas
        sensitive_keys = ["api_key", "apiKey", "key", "token", "password", "secret"]
        
        # Remover ou mascarar chaves sensíveis
        for key in list(sanitized.keys()):
            if key.lower() in [k.lower() for k in sensitive_keys]:
                sanitized[key] = "***REDACTED***"
            elif isinstance(sanitized[key], dict):
                sanitized[key] = self._sanitize_data(sanitized[key])
            elif isinstance(sanitized[key], list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in sanitized[key]
                ]
        
        return sanitized
    
    async def proxy_request(
        self,
        service_name: str,
        endpoint_key: str,
        client_id: Union[str, UUID],
        user_id: Optional[Union[str, UUID]],
        request_data: Dict[str, Any],
        method: str = "POST",
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Encaminha uma requisição para um serviço externo.
        
        Args:
            service_name: Nome do serviço.
            endpoint_key: Chave do endpoint no dicionário de endpoints do serviço.
            client_id: ID do cliente.
            user_id: ID do usuário.
            request_data: Dados da requisição.
            method: Método HTTP (GET, POST, etc.).
            additional_headers: Cabeçalhos adicionais para a requisição.
            
        Returns:
            Resposta do serviço externo.
            
        Raises:
            ValueError: Se o serviço ou endpoint não for suportado.
            Exception: Se ocorrer um erro na requisição.
        """
        start_time = time.time()
        error = None
        status_code = 500
        response_data = {}
        
        try:
            # Obter configuração do serviço
            service_config = await self._get_service_config(service_name)
            
            # Verificar se o endpoint é suportado
            if endpoint_key not in service_config["endpoints"]:
                raise ValueError(f"Endpoint não suportado para o serviço {service_name}: {endpoint_key}")
            
            # Obter credencial do cliente
            api_key = await self._get_credential(service_name, client_id)
            
            # Construir URL completa
            base_url = service_config["base_url"]
            endpoint_path = service_config["endpoints"][endpoint_key]
            url = f"{base_url}{endpoint_path}"
            
            # Preparar cabeçalhos
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # Adicionar cabeçalhos adicionais, se fornecidos
            if additional_headers:
                headers.update(additional_headers)
            
            # Fazer a requisição
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=request_data, headers=headers)
                else:  # POST é o padrão
                    response = await client.post(url, json=request_data, headers=headers)
                
                # Obter código de status e dados da resposta
                status_code = response.status_code
                response_data = response.json() if response.text else {}
                
                # Verificar se a requisição foi bem-sucedida
                response.raise_for_status()
                
                return response_data
        
        except httpx.HTTPStatusError as e:
            error = f"Erro HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Erro ao encaminhar requisição para {service_name}: {error}")
            raise ValueError(f"Erro ao acessar serviço externo: {error}")
        
        except httpx.RequestError as e:
            error = f"Erro de requisição: {str(e)}"
            logger.error(f"Erro ao encaminhar requisição para {service_name}: {error}")
            raise ValueError(f"Erro ao acessar serviço externo: {error}")
        
        except Exception as e:
            error = str(e)
            logger.error(f"Erro ao encaminhar requisição para {service_name}: {error}")
            raise
        
        finally:
            # Calcular tempo de execução
            execution_time = time.time() - start_time
            
            # Rastrear uso
            await self._track_usage(
                service_name=service_name,
                endpoint=endpoint_key,
                client_id=client_id,
                user_id=user_id,
                request_data=request_data,
                response_data=response_data,
                execution_time=execution_time,
                status_code=status_code,
                error=error
            )
    
    async def tavily_search(
        self,
        client_id: Union[str, UUID],
        user_id: Optional[Union[str, UUID]],
        query: str,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Realiza uma busca usando o Tavily.
        
        Args:
            client_id: ID do cliente.
            user_id: ID do usuário.
            query: Consulta de busca.
            search_depth: Profundidade da busca ("basic" ou "advanced").
            include_domains: Lista de domínios a serem incluídos.
            exclude_domains: Lista de domínios a serem excluídos.
            max_results: Número máximo de resultados.
            
        Returns:
            Resultados da busca.
        """
        # Preparar dados da requisição
        request_data = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results
        }
        
        # Adicionar domínios a incluir/excluir, se fornecidos
        if include_domains:
            request_data["include_domains"] = include_domains
        if exclude_domains:
            request_data["exclude_domains"] = exclude_domains
        
        # Encaminhar requisição
        return await self.proxy_request(
            service_name="tavily",
            endpoint_key="search",
            client_id=client_id,
            user_id=user_id,
            request_data=request_data
        )
    
    async def firecrawl_crawl(
        self,
        client_id: Union[str, UUID],
        user_id: Optional[Union[str, UUID]],
        url: str,
        max_pages: int = 10,
        max_depth: int = 2,
        follow_links: bool = True,
        javascript: bool = True
    ) -> Dict[str, Any]:
        """Realiza um crawling usando o Firecrawl.
        
        Args:
            client_id: ID do cliente.
            user_id: ID do usuário.
            url: URL a ser crawleada.
            max_pages: Número máximo de páginas.
            max_depth: Profundidade máxima do crawling.
            follow_links: Se deve seguir links.
            javascript: Se deve executar JavaScript.
            
        Returns:
            Resultados do crawling.
        """
        # Preparar dados da requisição
        request_data = {
            "url": url,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "follow_links": follow_links,
            "javascript": javascript
        }
        
        # Encaminhar requisição
        return await self.proxy_request(
            service_name="firecrawl",
            endpoint_key="crawl",
            client_id=client_id,
            user_id=user_id,
            request_data=request_data
        )
    
    async def firecrawl_extract(
        self,
        client_id: Union[str, UUID],
        user_id: Optional[Union[str, UUID]],
        url: str,
        javascript: bool = True,
        extract_links: bool = True,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """Extrai conteúdo de uma página usando o Firecrawl.
        
        Args:
            client_id: ID do cliente.
            user_id: ID do usuário.
            url: URL da página.
            javascript: Se deve executar JavaScript.
            extract_links: Se deve extrair links.
            extract_metadata: Se deve extrair metadados.
            
        Returns:
            Conteúdo extraído da página.
        """
        # Preparar dados da requisição
        request_data = {
            "url": url,
            "javascript": javascript,
            "extract_links": extract_links,
            "extract_metadata": extract_metadata
        }
        
        # Encaminhar requisição
        return await self.proxy_request(
            service_name="firecrawl",
            endpoint_key="extract",
            client_id=client_id,
            user_id=user_id,
            request_data=request_data
        )


# Instância global do serviço de proxy
proxy_service = ProxyService.get_instance()
"""