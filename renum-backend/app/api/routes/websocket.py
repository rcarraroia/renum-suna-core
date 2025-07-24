"""
Rotas WebSocket para comunicação em tempo real.

Este módulo implementa os endpoints WebSocket para comunicação em tempo real
entre o backend e o frontend, incluindo monitoramento de execuções, notificações
e atualizações de sistema.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, Path, HTTPException
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.core.auth import get_user_id_from_token
from app.core.dependencies import (
    get_websocket_manager,
    get_team_orchestrator,
    get_websocket_channel_service,
    get_websocket_resilience_service
)
from app.services.websocket_manager import WebSocketManager
from app.services.websocket_channel_service import WebSocketChannelService
from app.services.websocket_resilience_service import WebSocketResilienceService
from app.services.team_orchestrator import TeamOrchestrator

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/auth")
async def websocket_auth(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    client_id: Optional[str] = Query(None, description="Client identifier"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    resilience_service: WebSocketResilienceService = Depends(get_websocket_resilience_service)
):
    """
    Endpoint WebSocket para autenticação e canal geral de notificações.
    
    Args:
        websocket: Conexão WebSocket
        token: Token de autenticação
        client_id: Identificador do cliente (opcional)
        websocket_manager: Gerenciador de WebSockets
        resilience_service: Serviço de resiliência WebSocket
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Informações do cliente
        client_info = {
            "client_id": client_id or "unknown",
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host
        }
        
        # Conecta o WebSocket com o serviço de resiliência
        await websocket_manager.connect(websocket, user_id, client_info, resilience_service)
        
        # Inscreve no canal de notificações do usuário
        notification_channel = f"ws:notification:{user_id}"
        await websocket_manager.subscribe(websocket, notification_channel)
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "WebSocket connection established"
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Verifica limites de taxa
            ip = client_info.get("ip", "unknown")
            rate_limit_result = await resilience_service.check_rate_limit(user_id, ip)
            
            if not rate_limit_result["allowed"]:
                await websocket.send_json({
                    "type": "rate_limit_exceeded",
                    "message": "Rate limit exceeded",
                    "details": rate_limit_result
                })
                continue
            
            # Processa comandos do cliente
            if "command" in data:
                command = data["command"]
                
                if command == "subscribe":
                    channel = data.get("channel")
                    if channel:
                        await websocket_manager.subscribe(websocket, channel)
                        await websocket.send_json({
                            "type": "subscription_success",
                            "channel": channel
                        })
                
                elif command == "unsubscribe":
                    channel = data.get("channel")
                    if channel:
                        await websocket_manager.unsubscribe(websocket, channel)
                        await websocket.send_json({
                            "type": "unsubscription_success",
                            "channel": channel
                        })
                
                elif command == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": data.get("data")
                    })
                
                # Comandos relacionados à resiliência
                elif command == "get_buffered_messages":
                    messages = await resilience_service.get_buffered_messages(user_id)
                    await websocket.send_json({
                        "type": "buffered_messages",
                        "count": len(messages),
                        "messages": messages
                    })
                
                elif command == "clear_buffered_messages":
                    await resilience_service.clear_buffered_messages(user_id)
                    await websocket.send_json({
                        "type": "buffered_messages_cleared"
                    })
                
                elif command == "reset_circuit_breaker":
                    resilience_service.reset_circuit(user_id)
                    await websocket.send_json({
                        "type": "circuit_breaker_reset"
                    })
            
            # Registra sucesso no circuit breaker
            resilience_service.record_success(user_id)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        # Registra falha no circuit breaker
        if 'user_id' in locals():
            resilience_service.record_failure(user_id)
        
        import logging
        logging.error(f"WebSocket error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        websocket_manager.disconnect(websocket)


@router.websocket("/ws/executions/{execution_id}")
async def websocket_execution_monitor(
    websocket: WebSocket,
    execution_id: UUID,
    token: str = Query(..., description="Authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    team_orchestrator: TeamOrchestrator = Depends(get_team_orchestrator),
    resilience_service: WebSocketResilienceService = Depends(get_websocket_resilience_service)
):
    """
    Endpoint WebSocket para monitoramento de execuções em tempo real.
    
    Args:
        websocket: Conexão WebSocket
        execution_id: ID da execução
        token: Token de autenticação
        websocket_manager: Gerenciador de WebSockets
        team_orchestrator: Orquestrador de equipes
        resilience_service: Serviço de resiliência WebSocket
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
        
        # Informações do cliente
        client_info = {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host,
            "execution_id": str(execution_id)
        }
        
        # Conecta o WebSocket com o serviço de resiliência
        await websocket_manager.connect(websocket, user_id, client_info, resilience_service)
        
        # Inscreve no canal da execução
        execution_channel = f"ws:execution:{execution_id}"
        await websocket_manager.subscribe(websocket, execution_channel)
        
        # Envia o status inicial
        await websocket.send_json({
            "type": "status_update",
            "data": status.dict()
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Verifica limites de taxa
            ip = client_info.get("ip", "unknown")
            rate_limit_result = await resilience_service.check_rate_limit(user_id, ip)
            
            if not rate_limit_result["allowed"]:
                await websocket.send_json({
                    "type": "rate_limit_exceeded",
                    "message": "Rate limit exceeded",
                    "details": rate_limit_result
                })
                continue
            
            # Processa comandos específicos da execução
            if "command" in data:
                command = data["command"]
                
                if command == "get_logs":
                    try:
                        limit = data.get("limit", 100)
                        offset = data.get("offset", 0)
                        logs = await team_orchestrator.get_execution_logs(
                            execution_id, user_id, limit, offset
                        )
                        await websocket.send_json({
                            "type": "logs_response",
                            "data": [log.dict() for log in logs]
                        })
                        
                        # Registra sucesso no circuit breaker
                        resilience_service.record_success(user_id)
                        
                    except Exception as e:
                        # Registra falha no circuit breaker
                        resilience_service.record_failure(user_id)
                        
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Error getting logs: {str(e)}"
                        })
                
                elif command == "stop_execution":
                    try:
                        success = await team_orchestrator.stop_execution(execution_id, user_id)
                        await websocket.send_json({
                            "type": "stop_response",
                            "success": success
                        })
                        
                        # Registra sucesso no circuit breaker
                        resilience_service.record_success(user_id)
                        
                    except Exception as e:
                        # Registra falha no circuit breaker
                        resilience_service.record_failure(user_id)
                        
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Error stopping execution: {str(e)}"
                        })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        # Registra falha no circuit breaker
        if 'user_id' in locals():
            resilience_service.record_failure(user_id)
        
        import logging
        logging.error(f"WebSocket error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        websocket_manager.disconnect(websocket)


@router.websocket("/ws/admin")
async def websocket_admin(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Endpoint WebSocket para administração do sistema.
    
    Args:
        websocket: Conexão WebSocket
        token: Token de autenticação
        websocket_manager: Gerenciador de WebSockets
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verifica se o usuário é administrador
        # TODO: Implementar verificação de permissão de administrador
        is_admin = True  # Temporário, deve ser substituído por verificação real
        
        if not is_admin:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Informações do cliente
        client_info = {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host,
            "role": "admin"
        }
        
        # Conecta o WebSocket
        await websocket_manager.connect(websocket, user_id, client_info)
        
        # Inscreve no canal de administração
        admin_channel = "ws:admin"
        await websocket_manager.subscribe(websocket, admin_channel)
        
        # Envia estatísticas iniciais
        await websocket.send_json({
            "type": "stats",
            "data": websocket_manager.get_connection_stats()
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Processa comandos de administração
            if "command" in data:
                command = data["command"]
                
                if command == "get_stats":
                    await websocket.send_json({
                        "type": "stats",
                        "data": websocket_manager.get_connection_stats()
                    })
                
                elif command == "broadcast":
                    message = data.get("message")
                    target_users = data.get("target_users")
                    exclude_users = data.get("exclude_users")
                    
                    if message:
                        if target_users:
                            # Envia para usuários específicos
                            for user_id in target_users:
                                await websocket_manager.send_personal_message(
                                    user_id, 
                                    {
                                        "type": "admin_message",
                                        "message": message
                                    }
                                )
                        else:
                            # Broadcast para todos
                            await websocket_manager.broadcast_to_all(
                                {
                                    "type": "admin_message",
                                    "message": message
                                },
                                exclude_users
                            )
                        
                        await websocket.send_json({
                            "type": "broadcast_response",
                            "success": True
                        })
                
                elif command == "disconnect_user":
                    target_user = data.get("user_id")
                    if target_user and target_user in websocket_manager.user_connections:
                        # Cria uma cópia da lista para evitar modificação durante iteração
                        connections = list(websocket_manager.user_connections[target_user])
                        for conn in connections:
                            websocket_manager.disconnect(conn)
                        
                        await websocket.send_json({
                            "type": "disconnect_response",
                            "success": True,
                            "user_id": target_user
                        })
                    else:
                        await websocket.send_json({
                            "type": "disconnect_response",
                            "success": False,
                            "error": "User not found or not connected"
                        })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        import logging
        logging.error(f"WebSocket error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        websocket_manager.disconnect(websocket)