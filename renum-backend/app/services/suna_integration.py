"""
Módulo que implementa a integração com o Suna Core para a Plataforma Renum.

Este módulo fornece funcionalidades para enriquecer prompts com contexto do RAG
e para comunicação com a API do Suna Core.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.semantic_search import semantic_search_service
from app.services.usage_tracking import usage_tracking_service

# Configurar logger
logger = logging.getLogger(__name__)

class PromptEnrichmentRequest(BaseModel):
    """Modelo para requisição de enriquecimento de prompt."""
    
    prompt: str
    query: str
    collection_ids: Optional[List[Union[str, UUID]]] = None
    client_id: UUID
    agent_id: Optional[UUID] = None
    max_tokens: int = 1500
    similarity_threshold: float = 0.7


class SunaIntegrationService:
    """Serviço para integração com o Suna Core."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de integração com o Suna Core."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de integração com o Suna Core."""
        self.suna_api_url = settings.SUNA_API_URL
        self.suna_api_key = settings.SUNA_API_KEY
        
        if not self.suna_api_url:
            logger.warning("SUNA_API_URL não configurada. A integração com o Suna Core pode não funcionar corretamente.")
        
        if not self.suna_api_key:
            logger.warning("SUNA_API_KEY não configurada. A integração com o Suna Core pode não funcionar corretamente.")
        
        # Cliente HTTP para comunicação com a API do Suna Core
        self.http_client = httpx.AsyncClient(
            base_url=self.suna_api_url,
            headers={"Authorization": f"Bearer {self.suna_api_key}"},
            timeout=60.0
        )
        
        logger.info("Serviço de integração com o Suna Core inicializado")
    
    async def enrich_prompt_with_rag(self, request: PromptEnrichmentRequest) -> Dict[str, Any]:
        """Enriquece um prompt com contexto do RAG.
        
        Args:
            request: Requisição de enriquecimento de prompt.
            
        Returns:
            Prompt enriquecido com contexto do RAG.
        """
        try:
            start_time = time.time()
            
            # Obter contexto relevante para a consulta
            context_result = await semantic_search_service.get_context_for_query(
                query=request.query,
                collection_ids=request.collection_ids,
                max_tokens=request.max_tokens,
                similarity_threshold=request.similarity_threshold
            )
            
            # Registrar uso dos documentos
            if context_result["chunks_used"]:
                for chunk in context_result["chunks_used"]:
                    await usage_tracking_service.track_document_usage(
                        document_id=chunk["document_id"],
                        client_id=request.client_id,
                        chunk_id=chunk["chunk_id"],
                        agent_id=request.agent_id
                    )
            
            # Construir prompt enriquecido
            context = context_result["context"]
            enriched_prompt = f"{request.prompt}\n\nContexto relevante:\n{context}"
            
            # Calcular tempo de execução
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "enriched_prompt": enriched_prompt,
                "original_prompt": request.prompt,
                "context_used": context,
                "chunks_used": context_result["chunks_used"],
                "execution_time_ms": execution_time_ms
            }
        except Exception as e:
            logger.error(f"Erro ao enriquecer prompt com RAG: {str(e)}")
            # Em caso de erro, retornar o prompt original
            return {
                "enriched_prompt": request.prompt,
                "original_prompt": request.prompt,
                "context_used": "",
                "chunks_used": [],
                "error": str(e),
                "execution_time_ms": 0
            }
    
    async def execute_agent(self, agent_id: Union[str, UUID], input_text: str, client_id: Union[str, UUID]) -> Dict[str, Any]:
        """Executa um agente no Suna Core.
        
        Args:
            agent_id: ID do agente a ser executado.
            input_text: Texto de entrada para o agente.
            client_id: ID do cliente.
            
        Returns:
            Resultado da execução do agente.
        """
        try:
            # Construir payload para a API do Suna Core
            payload = {
                "agent_id": str(agent_id),
                "input": input_text,
                "client_id": str(client_id)
            }
            
            # Fazer requisição para a API do Suna Core
            response = await self.http_client.post("/agents/execute", json=payload)
            response.raise_for_status()
            
            # Processar resposta
            result = response.json()
            
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao executar agente: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erro ao executar agente: {str(e)}")
            raise
    
    async def get_agent_status(self, execution_id: Union[str, UUID]) -> Dict[str, Any]:
        """Obtém o status de uma execução de agente.
        
        Args:
            execution_id: ID da execução do agente.
            
        Returns:
            Status da execução do agente.
        """
        try:
            # Fazer requisição para a API do Suna Core
            response = await self.http_client.get(f"/agents/executions/{execution_id}")
            response.raise_for_status()
            
            # Processar resposta
            result = response.json()
            
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao obter status do agente: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erro ao obter status do agente: {str(e)}")
            raise
    
    async def close(self):
        """Fecha o cliente HTTP."""
        await self.http_client.aclose()


# Instância global do serviço de integração com o Suna Core
suna_integration_service = SunaIntegrationService.get_instance()