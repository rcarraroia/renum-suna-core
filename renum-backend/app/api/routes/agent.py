"""
Módulo que implementa as rotas da API para gerenciamento de agentes da Plataforma Renum.
Este módulo contém os endpoints para criar, atualizar, excluir e listar agentes,
bem como para executar agentes e gerenciar suas execuções.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from app.api.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentExecutionCreate,
    AgentExecutionUpdate,
    AgentExecutionResponse,
    AgentListResponse,
    AgentExecutionListResponse,
    PaginationParams
)
from app.models.agent import AgentStatus, AgentExecutionStatus
from app.services.agent import agent_service
from app.api.dependencies.auth import get_current_user

# Configurar logger
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(tags=["agents"])

# Rotas para Agentes

@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user = Depends(get_current_user)
):
    """Cria um novo agente.
    
    Args:
        agent_data: Dados do agente a ser criado.
        current_user: Usuário autenticado.
        
    Returns:
        O agente criado.
    """
    try:
        agent = await agent_service.create_agent(
            name=agent_data.name,
            client_id=current_user.client_id,
            configuration=agent_data.configuration,
            description=agent_data.description,
            knowledge_base_ids=agent_data.knowledge_base_ids,
            created_by=current_user.id,
            status=agent_data.status,
            metadata=agent_data.metadata
        )
        return agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar agente")

@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    client_id: Optional[UUID] = Query(None, description="Filtrar por ID do cliente"),
    status: Optional[AgentStatus] = Query(None, description="Filtrar por status"),
    knowledge_base_id: Optional[UUID] = Query(None, description="Filtrar por ID da base de conhecimento"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de agentes a serem retornados"),
    offset: int = Query(0, ge=0, description="Número de agentes a serem pulados"),
    current_user = Depends(get_current_user)
):
    """Lista agentes com filtros opcionais.
    
    Args:
        client_id: ID do cliente para filtrar (opcional).
        status: Status dos agentes para filtrar (opcional).
        knowledge_base_id: ID da base de conhecimento para filtrar (opcional).
        limit: Número máximo de agentes a serem retornados.
        offset: Número de agentes a serem pulados.
        current_user: Usuário autenticado.
        
    Returns:
        Lista de agentes que correspondem aos filtros.
    """
    try:
        # Se o usuário não for admin, forçar o filtro por client_id
        if not current_user.is_admin():
            client_id = current_user.client_id
        
        agents = await agent_service.list_agents(
            client_id=client_id,
            status=status,
            knowledge_base_id=knowledge_base_id,
            limit=limit,
            offset=offset
        )
        
        # Calcular o total de agentes (em uma implementação real, isso seria feito de forma mais eficiente)
        total = len(agents)
        if limit < total or offset > 0:
            # Se há paginação, precisamos de uma contagem mais precisa
            # Isso é apenas um exemplo simplificado
            total = total + offset
        
        return AgentListResponse(
            items=agents,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Erro ao listar agentes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar agentes")

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID = Path(..., description="ID do agente"),
    current_user = Depends(get_current_user)
):
    """Recupera um agente pelo ID.
    
    Args:
        agent_id: ID do agente.
        current_user: Usuário autenticado.
        
    Returns:
        O agente encontrado.
    """
    try:
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
        
        # Verificar permissão
        if not current_user.is_admin() and agent.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este agente")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao recuperar agente")

@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_data: AgentUpdate,
    agent_id: UUID = Path(..., description="ID do agente"),
    current_user = Depends(get_current_user)
):
    """Atualiza um agente existente.
    
    Args:
        agent_data: Dados atualizados do agente.
        agent_id: ID do agente a ser atualizado.
        current_user: Usuário autenticado.
        
    Returns:
        O agente atualizado.
    """
    try:
        # Verificar se o agente existe e se o usuário tem permissão
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
        
        # Verificar permissão
        if not current_user.is_admin() and agent.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este agente")
        
        # Atualizar agente
        updated_agent = await agent_service.update_agent(
            agent_id=agent_id,
            name=agent_data.name,
            description=agent_data.description,
            configuration=agent_data.configuration,
            status=agent_data.status,
            knowledge_base_ids=agent_data.knowledge_base_ids,
            updated_by=current_user.id,
            metadata=agent_data.metadata
        )
        
        return updated_agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar agente")

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID = Path(..., description="ID do agente"),
    current_user = Depends(get_current_user)
):
    """Exclui um agente.
    
    Args:
        agent_id: ID do agente a ser excluído.
        current_user: Usuário autenticado.
        
    Returns:
        204 No Content
    """
    try:
        # Verificar se o agente existe e se o usuário tem permissão
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
        
        # Verificar permissão
        if not current_user.is_admin() and agent.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este agente")
        
        # Excluir agente
        success = await agent_service.delete_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao excluir agente")
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao excluir agente")

@router.patch("/agents/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    status: AgentStatus,
    agent_id: UUID = Path(..., description="ID do agente"),
    current_user = Depends(get_current_user)
):
    """Atualiza o status de um agente.
    
    Args:
        status: Novo status do agente.
        agent_id: ID do agente.
        current_user: Usuário autenticado.
        
    Returns:
        O agente atualizado.
    """
    try:
        # Verificar se o agente existe e se o usuário tem permissão
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
        
        # Verificar permissão
        if not current_user.is_admin() and agent.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este agente")
        
        # Atualizar status
        updated_agent = await agent_service.update_agent_status(
            agent_id=agent_id,
            status=status,
            updated_by=current_user.id
        )
        
        return updated_agent
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar status do agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar status do agente")

# Rotas para Execuções de Agentes

@router.post("/agents/{agent_id}/execute", response_model=AgentExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_agent(
    execution_data: AgentExecutionCreate,
    agent_id: UUID = Path(..., description="ID do agente"),
    current_user = Depends(get_current_user)
):
    """Inicia a execução de um agente.
    
    Args:
        execution_data: Dados de entrada para a execução.
        agent_id: ID do agente a ser executado.
        current_user: Usuário autenticado.
        
    Returns:
        A execução criada.
    """
    try:
        # Verificar se o agente existe e se o usuário tem permissão
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
        
        # Verificar permissão
        if not current_user.is_admin() and agent.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este agente")
        
        # Iniciar execução
        execution = await agent_service.execute_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            input_data=execution_data.input,
            metadata=execution_data.metadata
        )
        
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao executar agente: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao executar agente")

@router.get("/executions", response_model=AgentExecutionListResponse)
async def list_executions(
    agent_id: Optional[UUID] = Query(None, description="Filtrar por ID do agente"),
    user_id: Optional[UUID] = Query(None, description="Filtrar por ID do usuário"),
    client_id: Optional[UUID] = Query(None, description="Filtrar por ID do cliente"),
    status: Optional[AgentExecutionStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de execuções a serem retornadas"),
    offset: int = Query(0, ge=0, description="Número de execuções a serem puladas"),
    current_user = Depends(get_current_user)
):
    """Lista execuções de agentes com filtros opcionais.
    
    Args:
        agent_id: ID do agente para filtrar (opcional).
        user_id: ID do usuário para filtrar (opcional).
        client_id: ID do cliente para filtrar (opcional).
        status: Status das execuções para filtrar (opcional).
        limit: Número máximo de execuções a serem retornadas.
        offset: Número de execuções a serem puladas.
        current_user: Usuário autenticado.
        
    Returns:
        Lista de execuções que correspondem aos filtros.
    """
    try:
        # Se o usuário não for admin, forçar o filtro por client_id
        if not current_user.is_admin():
            client_id = current_user.client_id
        
        executions = await agent_service.list_executions(
            agent_id=agent_id,
            user_id=user_id,
            client_id=client_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Calcular o total de execuções (em uma implementação real, isso seria feito de forma mais eficiente)
        total = len(executions)
        if limit < total or offset > 0:
            # Se há paginação, precisamos de uma contagem mais precisa
            # Isso é apenas um exemplo simplificado
            total = total + offset
        
        return AgentExecutionListResponse(
            items=executions,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Erro ao listar execuções: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar execuções")

@router.get("/executions/{execution_id}", response_model=AgentExecutionResponse)
async def get_execution(
    execution_id: UUID = Path(..., description="ID da execução"),
    current_user = Depends(get_current_user)
):
    """Recupera uma execução pelo ID.
    
    Args:
        execution_id: ID da execução.
        current_user: Usuário autenticado.
        
    Returns:
        A execução encontrada.
    """
    try:
        execution = await agent_service.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execução não encontrada")
        
        # Verificar permissão
        if not current_user.is_admin() and execution.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a esta execução")
        
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar execução: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao recuperar execução")

@router.patch("/executions/{execution_id}/cancel", response_model=AgentExecutionResponse)
async def cancel_execution(
    execution_id: UUID = Path(..., description="ID da execução"),
    current_user = Depends(get_current_user)
):
    """Cancela uma execução em andamento.
    
    Args:
        execution_id: ID da execução a ser cancelada.
        current_user: Usuário autenticado.
        
    Returns:
        A execução atualizada.
    """
    try:
        # Verificar se a execução existe e se o usuário tem permissão
        execution = await agent_service.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execução não encontrada")
        
        # Verificar permissão
        if not current_user.is_admin() and execution.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a esta execução")
        
        # Cancelar execução
        cancelled_execution = await agent_service.cancel_execution(execution_id)
        
        return cancelled_execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar execução: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao cancelar execução")
"""