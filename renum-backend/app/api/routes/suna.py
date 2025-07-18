"""
Módulo que implementa os endpoints REST para integração com o Suna Core.

Este módulo contém os endpoints para enriquecimento de prompts com contexto do RAG
e para execução de agentes no Suna Core.
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.schemas.suna import (
    PromptEnrichmentRequest,
    PromptEnrichmentResponse,
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentStatusRequest,
    AgentStatusResponse
)
from app.services.suna_integration import suna_integration_service

# Configurar logger
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/suna",
    tags=["Suna Integration"],
    responses={404: {"description": "Item não encontrado"}}
)


@router.post("/enrich-prompt", response_model=PromptEnrichmentResponse)
async def enrich_prompt(request: PromptEnrichmentRequest):
    """Enriquece um prompt com contexto do RAG."""
    try:
        # Converter para o modelo interno
        internal_request = request.model_dump()
        
        # Enriquecer prompt com contexto do RAG
        result = await suna_integration_service.enrich_prompt_with_rag(request)
        
        return result
    except Exception as e:
        logger.error(f"Erro ao enriquecer prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enriquecer prompt: {str(e)}"
        )


@router.post("/execute-agent", response_model=AgentExecutionResponse)
async def execute_agent(request: AgentExecutionRequest):
    """Executa um agente no Suna Core."""
    try:
        start_time = time.time()
        
        # Se solicitado, enriquecer o prompt com contexto do RAG
        input_text = request.input
        rag_context_used = False
        
        if request.enrich_with_rag and request.rag_query:
            # Criar requisição de enriquecimento
            enrichment_request = PromptEnrichmentRequest(
                prompt=request.input,
                query=request.rag_query,
                collection_ids=request.collection_ids,
                client_id=request.client_id,
                agent_id=request.agent_id
            )
            
            # Enriquecer prompt
            enrichment_result = await suna_integration_service.enrich_prompt_with_rag(enrichment_request)
            
            # Usar prompt enriquecido
            input_text = enrichment_result["enriched_prompt"]
            rag_context_used = True
        
        # Executar agente
        result = await suna_integration_service.execute_agent(
            agent_id=request.agent_id,
            input_text=input_text,
            client_id=request.client_id
        )
        
        # Calcular tempo de execução
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Formatar resposta
        response = {
            "execution_id": result.get("execution_id"),
            "status": result.get("status"),
            "output": result.get("output"),
            "error": result.get("error"),
            "rag_context_used": rag_context_used,
            "execution_time_ms": execution_time_ms
        }
        
        return response
    except Exception as e:
        logger.error(f"Erro ao executar agente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar agente: {str(e)}"
        )


@router.get("/agent-status/{execution_id}", response_model=AgentStatusResponse)
async def get_agent_status(execution_id: str):
    """Obtém o status de uma execução de agente."""
    try:
        # Obter status do agente
        result = await suna_integration_service.get_agent_status(execution_id)
        
        # Formatar resposta
        response = {
            "execution_id": result.get("execution_id"),
            "status": result.get("status"),
            "agent_id": result.get("agent_id"),
            "input": result.get("input"),
            "output": result.get("output"),
            "error": result.get("error"),
            "started_at": result.get("started_at"),
            "completed_at": result.get("completed_at"),
            "execution_time_ms": result.get("execution_time_ms")
        }
        
        return response
    except Exception as e:
        logger.error(f"Erro ao obter status do agente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter status do agente: {str(e)}"
        )