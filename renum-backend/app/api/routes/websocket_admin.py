"""
Rotas administrativas para WebSocket
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.websocket_admin_service import WebSocketAdminService, ConnectionInfo
from app.core.auth import get_current_admin_user
from app.core.dependencies import get_websocket_admin_service

router = APIRouter(prefix="/admin/websocket", tags=["WebSocket Admin"])

class DisconnectRequest(BaseModel):
    """Request para desconectar conexão"""
    reason: Optional[str] = "Admin disconnect"

class BroadcastRequest(BaseModel):
    """Request para broadcast administrativo"""
    message: str
    target_type: str = "all"  # "all", "user", "channel"
    target_id: Optional[str] = None

class ConnectionResponse(BaseModel):
    """Response com informações de conexão"""
    connection_id: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    connected_at: str
    last_activity: str
    channels: List[str]
    message_count: int
    bytes_sent: int
    bytes_received: int
    status: str

class StatsResponse(BaseModel):
    """Response com estatísticas"""
    total_connections: int
    active_connections: int
    idle_connections: int
    authenticated_connections: int
    anonymous_connections: int
    total_channels: int
    total_messages_sent: int
    total_bytes_transferred: int
    average_connection_duration: float
    peak_connections: int
    peak_connections_time: Optional[str]

@router.get("/connections", response_model=List[ConnectionResponse])
async def get_active_connections(
    user_id: Optional[str] = Query(None, description="Filtrar por usuário"),
    limit: Optional[int] = Query(50, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginação"),
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém lista de conexões ativas"""
    try:
        connections = await admin_service.get_active_connections(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return [
            ConnectionResponse(**conn.to_dict())
            for conn in connections
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter conexões: {str(e)}")

@router.get("/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection_details(
    connection_id: str,
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém detalhes de uma conexão específica"""
    try:
        connection = await admin_service.get_connection_by_id(connection_id)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Conexão não encontrada")
        
        return ConnectionResponse(**connection.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter conexão: {str(e)}")

@router.get("/users/{user_id}/connections", response_model=List[ConnectionResponse])
async def get_user_connections(
    user_id: str,
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém todas as conexões de um usuário"""
    try:
        connections = await admin_service.get_connections_by_user(user_id)
        
        return [
            ConnectionResponse(**conn.to_dict())
            for conn in connections
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter conexões do usuário: {str(e)}")

@router.get("/stats", response_model=StatsResponse)
async def get_connection_stats(
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém estatísticas atuais das conexões"""
    try:
        stats = await admin_service.get_connection_stats()
        
        return StatsResponse(
            total_connections=stats.total_connections,
            active_connections=stats.active_connections,
            idle_connections=stats.idle_connections,
            authenticated_connections=stats.authenticated_connections,
            anonymous_connections=stats.anonymous_connections,
            total_channels=stats.total_channels,
            total_messages_sent=stats.total_messages_sent,
            total_bytes_transferred=stats.total_bytes_transferred,
            average_connection_duration=stats.average_connection_duration,
            peak_connections=stats.peak_connections,
            peak_connections_time=stats.peak_connections_time.isoformat() if stats.peak_connections_time else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.get("/stats/history")
async def get_stats_history(
    hours: int = Query(24, description="Horas de histórico"),
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém histórico de estatísticas"""
    try:
        history = await admin_service.get_stats_history(hours=hours)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")

@router.get("/channels")
async def get_channel_info(
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Obtém informações sobre canais ativos"""
    try:
        channels = await admin_service.get_channel_info()
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canais: {str(e)}")

@router.post("/connections/{connection_id}/disconnect")
async def disconnect_connection(
    connection_id: str,
    request: DisconnectRequest,
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Desconecta uma conexão específica"""
    try:
        success = await admin_service.disconnect_connection(
            connection_id=connection_id,
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conexão não encontrada ou já desconectada")
        
        return {"message": "Conexão desconectada com sucesso", "connection_id": connection_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desconectar: {str(e)}")

@router.post("/users/{user_id}/disconnect")
async def disconnect_user_connections(
    user_id: str,
    request: DisconnectRequest,
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Desconecta todas as conexões de um usuário"""
    try:
        disconnected_count = await admin_service.disconnect_user_connections(
            user_id=user_id,
            reason=request.reason
        )
        
        return {
            "message": f"Desconectadas {disconnected_count} conexões do usuário",
            "user_id": user_id,
            "disconnected_count": disconnected_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desconectar usuário: {str(e)}")

@router.post("/broadcast")
async def broadcast_admin_message(
    request: BroadcastRequest,
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Envia mensagem administrativa"""
    try:
        sent_count = await admin_service.broadcast_admin_message(
            message=request.message,
            target_type=request.target_type,
            target_id=request.target_id
        )
        
        return {
            "message": "Mensagem enviada com sucesso",
            "sent_count": sent_count,
            "target_type": request.target_type,
            "target_id": request.target_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {str(e)}")

@router.delete("/connections/cleanup")
async def cleanup_stale_connections(
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Remove conexões obsoletas"""
    try:
        await admin_service.cleanup_stale_connections()
        return {"message": "Limpeza de conexões obsoletas concluída"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")

@router.get("/health")
async def websocket_health_check(
    admin_service: WebSocketAdminService = Depends(get_websocket_admin_service),
    current_admin = Depends(get_current_admin_user)
):
    """Verifica saúde do sistema WebSocket"""
    try:
        stats = await admin_service.get_connection_stats()
        
        # Determinar status de saúde
        health_status = "healthy"
        issues = []
        
        # Verificar se há muitas conexões inativas
        if stats.total_connections > 0:
            idle_percentage = (stats.idle_connections / stats.total_connections) * 100
            if idle_percentage > 50:
                health_status = "warning"
                issues.append(f"Alto percentual de conexões inativas: {idle_percentage:.1f}%")
        
        # Verificar se há pico de conexões
        if stats.total_connections > stats.peak_connections * 0.9:
            health_status = "warning"
            issues.append("Próximo ao pico de conexões")
        
        return {
            "status": health_status,
            "total_connections": stats.total_connections,
            "active_connections": stats.active_connections,
            "idle_connections": stats.idle_connections,
            "issues": issues,
            "timestamp": admin_service.websocket_manager.get_current_time().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": admin_service.websocket_manager.get_current_time().isoformat()
        }