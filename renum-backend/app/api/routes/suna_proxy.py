"""
Módulo que implementa os endpoints de proxy para a API da Suna Core.

Este módulo fornece endpoints para proxying de chamadas para a Suna Core,
incluindo execução de agentes e callbacks de ferramentas.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from fastapi.security import OAuth2PasswordBearer

from app.api.schemas.agent import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentExecutionStatusResponse,
    ToolCallbackRequest,
    ToolCallbackResponse
)
from app.services.suna_integration import suna_integration_service
from app.services.tool_proxy import tool_proxy
from app.services.suna_client import suna_client
from app.api.dependencies.auth import get_current_user, get_current_client

# Configurar logger
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/api/suna",
    tags=["suna"],
    responses={404: {"description": "Not found"}},
)

# Endpoint para executar um agente
@router.post("/agent/{agent_id}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_id: UUID,
    request: AgentExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Executa um agente na Suna Core.
    
    Args:
        agent_id: ID do agente a ser executado.
        request: Dados da requisição.
        current_user: Usuário autenticado.
        
    Returns:
        Dados da execução criada.
        
    Raises:
        HTTPException: Se ocorrer um erro na execução.
    """
    try:
        execution = await suna_integration_service.execute_agent(
            agent_id=agent_id,
            user_id=current_user["id"],
            prompt=request.prompt,
            metadata=request.metadata
        )
        
        return {
            "execution_id": execution.id,
            "status": execution.status,
            "created_at": execution.created_at,
            "message": "Execução iniciada com sucesso"
        }
    except ValueError as e:
        logger.error(f"Erro ao executar agente: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao executar agente: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao executar agente")

# Endpoint para obter o status de uma execução
@router.get("/execution/{execution_id}", response_model=AgentExecutionStatusResponse)
async def get_execution_status(
    execution_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtém o status de uma execução.
    
    Args:
        execution_id: ID da execução.
        current_user: Usuário autenticado.
        
    Returns:
        Status da execução.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        execution = await suna_integration_service.get_execution_status(execution_id)
        
        # Verificar se o usuário tem acesso à execução
        if str(execution.user_id) != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado a esta execução")
        
        return {
            "execution_id": execution.id,
            "agent_id": execution.agent_id,
            "status": execution.status,
            "created_at": execution.created_at,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "output": execution.output,
            "error": execution.error,
            "tokens_used": execution.tokens_used
        }
    except ValueError as e:
        logger.error(f"Erro ao obter status da execução: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao obter status da execução: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao obter status da execução")

# Endpoint para cancelar uma execução
@router.post("/execution/{execution_id}/cancel", response_model=AgentExecutionStatusResponse)
async def cancel_execution(
    execution_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancela uma execução em andamento.
    
    Args:
        execution_id: ID da execução.
        current_user: Usuário autenticado.
        
    Returns:
        Status da execução.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        execution = await suna_integration_service.cancel_execution(execution_id)
        
        # Verificar se o usuário tem acesso à execução
        if str(execution.user_id) != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado a esta execução")
        
        return {
            "execution_id": execution.id,
            "agent_id": execution.agent_id,
            "status": execution.status,
            "created_at": execution.created_at,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "output": execution.output,
            "error": execution.error,
            "tokens_used": execution.tokens_used
        }
    except ValueError as e:
        logger.error(f"Erro ao cancelar execução: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao cancelar execução: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao cancelar execução")

# Endpoint para callback de ferramentas
@router.post("/proxy/tool/{tool_name}", response_model=ToolCallbackResponse)
async def tool_callback(
    tool_name: str,
    request: ToolCallbackRequest = Body(...),
):
    """Manipula um callback de ferramenta da Suna Core.
    
    Args:
        tool_name: Nome da ferramenta.
        request: Dados da requisição.
        
    Returns:
        Resultado da chamada da ferramenta.
        
    Raises:
        HTTPException: Se ocorrer um erro na chamada da ferramenta.
    """
    try:
        # Verificar se a ferramenta é suportada
        if tool_name not in tool_proxy.supported_tools:
            raise HTTPException(status_code=400, detail=f"Ferramenta não suportada: {tool_name}")
        
        # Verificar se o execution_id foi fornecido
        if not request.execution_id:
            raise HTTPException(status_code=400, detail="execution_id é obrigatório")
        
        # Fazer proxy da chamada da ferramenta
        result = await suna_integration_service.handle_tool_callback(
            tool_name=tool_name,
            execution_id=request.execution_id,
            parameters=request.parameters
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        logger.error(f"Erro no callback de ferramenta: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no callback de ferramenta: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no callback de ferramenta")

# Endpoint para verificar a saúde da Suna Core
@router.get("/health")
async def health_check():
    """Verifica se a API da Suna Core está disponível.
    
    Returns:
        Status da API da Suna Core.
        
    Raises:
        HTTPException: Se a API da Suna Core não estiver disponível.
    """
    try:
        is_healthy = await suna_client.health_check()
        
        if not is_healthy:
            raise HTTPException(status_code=503, detail="Suna Core não está disponível")
        
        return {"status": "ok", "message": "Suna Core está disponível"}
    except Exception as e:
        logger.error(f"Erro no health check da Suna Core: {str(e)}")
        raise HTTPException(status_code=503, detail="Erro ao verificar saúde da Suna Core")

# Endpoint para obter ferramentas disponíveis
@router.get("/tools")
async def get_available_tools(
    current_client: Dict[str, Any] = Depends(get_current_client)
):
    """Obtém a lista de ferramentas disponíveis para o cliente.
    
    Args:
        current_client: Cliente autenticado.
        
    Returns:
        Lista de ferramentas disponíveis.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        tools = await tool_proxy.get_available_tools(current_client["id"])
        
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Erro ao obter ferramentas disponíveis: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao obter ferramentas disponíveis")

# Endpoint para obter modelos disponíveis
@router.get("/models")
async def get_available_models():
    """Obtém a lista de modelos disponíveis na Suna Core.
    
    Returns:
        Lista de modelos disponíveis.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        models = await suna_client.get_available_models()
        
        return {"models": models}
    except Exception as e:
        logger.error(f"Erro ao obter modelos disponíveis: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao obter modelos disponíveis")