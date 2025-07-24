"""
Rotas da API para execução de equipes de agentes.

Este módulo implementa os endpoints da API para execução de equipes de agentes,
incluindo iniciar, monitorar e parar execuções.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from typing import List, Optional
from uuid import UUID

from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    ExecutionStatus,
    ExecutionLogEntry,
    ExecutionStatusResponse
)
from app.services.team_orchestrator import TeamOrchestrator
# from app.repositories.team_execution_repository import TeamExecutionRepository
from app.core.dependencies import get_team_orchestrator, get_team_execution_repository, get_websocket_manager
from app.core.auth import get_current_user_id, get_user_id_from_token
from app.core.validators import validate_execution_limits

router = APIRouter(tags=["team-executions"])


@router.post("/teams/{team_id}/execute", response_model=TeamExecutionResponse)
async def execute_team(
    execution_data: TeamExecutionCreate,
    team_id: UUID = Path(..., description="Team ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator),
    # team_execution_repository: TeamExecutionRepository = Depends(get_team_execution_repository)
):
    """
    Inicia a execução de uma equipe.
    
    Args:
        execution_data: Dados da execução
        team_id: ID da equipe
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        team_execution_repository: Repositório de execuções de equipes
        
    Returns:
        Objeto TeamExecutionResponse com os dados da execução criada
        
    Raises:
        HTTPException: Se ocorrer um erro na execução da equipe
    """
    # Verifica se o team_id no path corresponde ao team_id no corpo da requisição
    if team_id != execution_data.team_id:
        raise HTTPException(status_code=400, detail="Team ID in path does not match Team ID in request body")
    
    try:
        # Valida os limites de execução
        await validate_execution_limits(user_id, team_execution_repository)
        
        # Executa a equipe
        return await team_orchestrator.execute_team(user_id, execution_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute team: {str(e)}")


@router.get("/executions", response_model=List[TeamExecutionResponse])
async def list_executions(
    team_id: Optional[UUID] = Query(None, description="Filter by Team ID"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator)
):
    """
    Lista execuções de equipe.
    
    Args:
        team_id: ID da equipe (opcional)
        limit: Limite de resultados
        offset: Deslocamento para paginação
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        
    Returns:
        Lista de objetos TeamExecutionResponse
    """
    try:
        return await team_orchestrator.list_executions(user_id, team_id, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: UUID = Path(..., description="Execution ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator)
):
    """
    Obtém o status de uma execução.
    
    Args:
        execution_id: ID da execução
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        
    Returns:
        Objeto TeamExecutionStatus com o status da execução
        
    Raises:
        HTTPException: Se a execução não existir ou o usuário não tiver acesso
    """
    status = await team_orchestrator.get_execution_status(execution_id, user_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return status


@router.get("/executions/{execution_id}/result", response_model=TeamExecutionResponse)
async def get_execution_result(
    execution_id: UUID = Path(..., description="Execution ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator)
):
    """
    Obtém o resultado de uma execução.
    
    Args:
        execution_id: ID da execução
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        
    Returns:
        Objeto TeamExecutionResult com o resultado da execução
        
    Raises:
        HTTPException: Se a execução não existir ou o usuário não tiver acesso
    """
    result = await team_orchestrator.get_execution_result(execution_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return result


@router.post("/executions/{execution_id}/stop", response_model=dict)
async def stop_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator)
):
    """
    Para uma execução em andamento.
    
    Args:
        execution_id: ID da execução
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        
    Returns:
        Dicionário com status da operação
        
    Raises:
        HTTPException: Se a execução não existir ou o usuário não tiver acesso
    """
    success = await team_orchestrator.stop_execution(execution_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found or not running")
    
    return {"status": "success", "message": f"Execution {execution_id} stopped"}


@router.delete("/executions/{execution_id}", response_model=dict)
async def delete_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator)
):
    """
    Exclui uma execução.
    
    Args:
        execution_id: ID da execução
        user_id: ID do usuário autenticado
        team_orchestrator: Orquestrador de equipes
        
    Returns:
        Dicionário com status da operação
        
    Raises:
        HTTPException: Se a execução não existir ou o usuário não tiver acesso
    """
    success = await team_orchestrator.delete_execution(execution_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return {"status": "success", "message": f"Execution {execution_id} deleted"}


@router.get("/executions/{execution_id}/logs", response_model=List[ExecutionLogEntry])
async def get_execution_logs(
    execution_id: UUID = Path(..., description="Execution ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    log_types: Optional[List[str]] = Query(None, description="Filter by log types"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    user_id: UUID = Depends(get_current_user_id),
    # execution_repository: TeamExecutionRepository = Depends(get_team_execution_repository)
):
    """
    Obtém logs de execução.
    
    Args:
        execution_id: ID da execução
        limit: Limite de resultados
        offset: Deslocamento para paginação
        log_types: Tipos de log a serem incluídos
        agent_id: Filtrar por agente específico
        user_id: ID do usuário autenticado
        execution_repository: Repositório de execuções
        
    Returns:
        Lista de objetos ExecutionLogEntry
        
    Raises:
        HTTPException: Se a execução não existir ou o usuário não tiver acesso
    """
    # Verifica se a execução existe e pertence ao usuário
    execution = await execution_repository.get_execution(execution_id, user_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    try:
        return await execution_repository.get_execution_logs(execution_id, limit, offset, log_types, agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution logs: {str(e)}")


@router.websocket("/ws/executions/{execution_id}/monitor")
async def monitor_execution(
    websocket: WebSocket,
    execution_id: UUID,
    token: str = Query(..., description="Authentication token"),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator),
    websocket_manager = Depends(get_websocket_manager)
):
    """
    WebSocket para monitoramento em tempo real da execução.
    
    Args:
        websocket: WebSocket connection
        execution_id: ID da execução
        token: Token de autenticação
        team_orchestrator: Orquestrador de equipes
        websocket_manager: Gerenciador de WebSockets
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verifica se a execução existe e pertence ao usuário
        status = await team_orchestrator.get_execution_status(execution_id, user_id)
        if not status:
            await websocket.close(code=1008, reason="Execution not found")
            return
        
        # Conecta o WebSocket
        await websocket_manager.connect(websocket, execution_id)
        
        # Envia o status inicial
        await websocket.send_json({
            "type": "status_update",
            "data": status.dict()
        })
        
        # Inscreve-se para atualizações da execução
        async for update in team_orchestrator.subscribe_to_execution_updates(execution_id):
            await websocket.send_json(update)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, execution_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        websocket_manager.disconnect(websocket, execution_id)
    finally:
        # Cleanup subscription
        await team_orchestrator.unsubscribe_from_execution_updates(execution_id)