"""
Rotas WebSocket para canais e salas.

Este módulo implementa os endpoints WebSocket para canais e salas,
permitindo a comunicação em tempo real entre usuários.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, Path, HTTPException
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.core.auth import get_user_id_from_token
from app.core.dependencies import get_websocket_manager, get_websocket_channel_service
from app.services.websocket_manager import WebSocketManager
from app.services.websocket_channel_service import WebSocketChannelService

router = APIRouter(tags=["websocket-channels"])


@router.websocket("/ws/channels/{channel_name}")
async def websocket_channel(
    websocket: WebSocket,
    channel_name: str,
    token: str = Query(..., description="Authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    channel_service: WebSocketChannelService = Depends(get_websocket_channel_service)
):
    """
    Endpoint WebSocket para canais.
    
    Args:
        websocket: Conexão WebSocket
        channel_name: Nome do canal
        token: Token de autenticação
        websocket_manager: Gerenciador de WebSockets
        channel_service: Serviço de canais WebSocket
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Informações do cliente
        client_info = {
            "client_id": websocket.headers.get("client-id", "unknown"),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host,
            "channel": channel_name
        }
        
        # Conecta o WebSocket
        await websocket_manager.connect(websocket, user_id, client_info)
        
        # Inscreve no canal
        success = await channel_service.subscribe_to_channel(channel_name, user_id)
        if not success:
            await websocket.close(code=1008, reason="Failed to subscribe to channel")
            return
        
        # Inscreve no canal WebSocket
        await websocket_manager.subscribe(websocket, f"ws:channel:{channel_name}")
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "channel_joined",
            "channel": channel_name,
            "message": f"Joined channel {channel_name}"
        })
        
        # Obtém a lista de assinantes
        subscribers = await channel_service.get_channel_subscribers(channel_name)
        
        # Envia a lista de assinantes
        await websocket.send_json({
            "type": "channel_subscribers",
            "channel": channel_name,
            "subscribers": subscribers
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Processa mensagens do cliente
            if "type" in data and data["type"] == "message" and "content" in data:
                # Adiciona informações do remetente
                message = {
                    "type": "channel_message",
                    "channel": channel_name,
                    "sender": user_id,
                    "content": data["content"],
                    "timestamp": data.get("timestamp")
                }
                
                # Publica a mensagem no canal
                await channel_service.publish_to_channel(channel_name, message)
            
            # Processa comandos do cliente
            elif "command" in data:
                command = data["command"]
                
                if command == "leave":
                    # Cancela a inscrição no canal
                    await channel_service.unsubscribe_from_channel(channel_name, user_id)
                    await websocket_manager.unsubscribe(websocket, f"ws:channel:{channel_name}")
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "channel_left",
                        "channel": channel_name,
                        "message": f"Left channel {channel_name}"
                    })
                    
                    break
                
                elif command == "get_subscribers":
                    # Obtém a lista de assinantes
                    subscribers = await channel_service.get_channel_subscribers(channel_name)
                    
                    # Envia a lista de assinantes
                    await websocket.send_json({
                        "type": "channel_subscribers",
                        "channel": channel_name,
                        "subscribers": subscribers
                    })
            
    except WebSocketDisconnect:
        # Cancela a inscrição no canal
        await channel_service.unsubscribe_from_channel(channel_name, user_id)
        websocket_manager.disconnect(websocket)
    except Exception as e:
        import logging
        logging.error(f"WebSocket channel error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        
        # Cancela a inscrição no canal
        await channel_service.unsubscribe_from_channel(channel_name, user_id)
        websocket_manager.disconnect(websocket)


@router.websocket("/ws/rooms/{room_name}")
async def websocket_room(
    websocket: WebSocket,
    room_name: str,
    token: str = Query(..., description="Authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    channel_service: WebSocketChannelService = Depends(get_websocket_channel_service)
):
    """
    Endpoint WebSocket para salas.
    
    Args:
        websocket: Conexão WebSocket
        room_name: Nome da sala
        token: Token de autenticação
        websocket_manager: Gerenciador de WebSockets
        channel_service: Serviço de canais WebSocket
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Informações do cliente
        client_info = {
            "client_id": websocket.headers.get("client-id", "unknown"),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host,
            "room": room_name
        }
        
        # Conecta o WebSocket
        await websocket_manager.connect(websocket, user_id, client_info)
        
        # Entra na sala
        success = await channel_service.join_room(room_name, user_id)
        if not success:
            await websocket.close(code=1008, reason="Failed to join room")
            return
        
        # Inscreve no canal WebSocket
        await websocket_manager.subscribe(websocket, f"ws:room:{room_name}")
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "room_joined",
            "room": room_name,
            "message": f"Joined room {room_name}"
        })
        
        # Obtém a lista de membros
        members = await channel_service.get_room_members(room_name)
        
        # Envia a lista de membros
        await websocket.send_json({
            "type": "room_members",
            "room": room_name,
            "members": members
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Processa mensagens do cliente
            if "type" in data and data["type"] == "message" and "content" in data:
                # Adiciona informações do remetente
                message = {
                    "type": "room_message",
                    "room": room_name,
                    "sender": user_id,
                    "content": data["content"],
                    "timestamp": data.get("timestamp")
                }
                
                # Publica a mensagem na sala
                await channel_service.publish_to_room(room_name, message)
            
            # Processa comandos do cliente
            elif "command" in data:
                command = data["command"]
                
                if command == "leave":
                    # Sai da sala
                    await channel_service.leave_room(room_name, user_id)
                    await websocket_manager.unsubscribe(websocket, f"ws:room:{room_name}")
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "room_left",
                        "room": room_name,
                        "message": f"Left room {room_name}"
                    })
                    
                    break
                
                elif command == "get_members":
                    # Obtém a lista de membros
                    members = await channel_service.get_room_members(room_name)
                    
                    # Envia a lista de membros
                    await websocket.send_json({
                        "type": "room_members",
                        "room": room_name,
                        "members": members
                    })
            
    except WebSocketDisconnect:
        # Sai da sala
        await channel_service.leave_room(room_name, user_id)
        websocket_manager.disconnect(websocket)
    except Exception as e:
        import logging
        logging.error(f"WebSocket room error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        
        # Sai da sala
        await channel_service.leave_room(room_name, user_id)
        websocket_manager.disconnect(websocket)


@router.websocket("/ws/user")
async def websocket_user(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    channel_service: WebSocketChannelService = Depends(get_websocket_channel_service)
):
    """
    Endpoint WebSocket para mensagens diretas ao usuário.
    
    Args:
        websocket: Conexão WebSocket
        token: Token de autenticação
        websocket_manager: Gerenciador de WebSockets
        channel_service: Serviço de canais WebSocket
    """
    try:
        # Valida o token e obtém o user_id
        user_id = await get_user_id_from_token(token)
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Informações do cliente
        client_info = {
            "client_id": websocket.headers.get("client-id", "unknown"),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "ip": websocket.client.host
        }
        
        # Conecta o WebSocket
        await websocket_manager.connect(websocket, user_id, client_info)
        
        # Inscreve no canal do usuário
        await websocket_manager.subscribe(websocket, f"ws:user:{user_id}")
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "User WebSocket connection established"
        })
        
        # Obtém as inscrições e salas do usuário
        subscriptions = await channel_service.get_user_subscriptions(user_id)
        rooms = await channel_service.get_user_rooms(user_id)
        
        # Envia as inscrições e salas
        await websocket.send_json({
            "type": "user_subscriptions",
            "subscriptions": subscriptions,
            "rooms": rooms
        })
        
        # Loop de recebimento de mensagens
        while True:
            data = await websocket.receive_json()
            
            # Processa comandos do cliente
            if "command" in data:
                command = data["command"]
                
                if command == "send_message" and "target_user" in data and "content" in data:
                    # Envia mensagem para outro usuário
                    target_user = data["target_user"]
                    
                    message = {
                        "type": "direct_message",
                        "sender": user_id,
                        "content": data["content"],
                        "timestamp": data.get("timestamp")
                    }
                    
                    # Publica a mensagem para o usuário alvo
                    await channel_service.publish_to_user(target_user, message)
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "message_sent",
                        "target_user": target_user,
                        "message_id": data.get("message_id")
                    })
                
                elif command == "join_channel" and "channel" in data:
                    # Inscreve no canal
                    channel = data["channel"]
                    success = await channel_service.subscribe_to_channel(channel, user_id)
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "channel_subscription",
                        "channel": channel,
                        "success": success,
                        "message": f"{'Subscribed to' if success else 'Failed to subscribe to'} channel {channel}"
                    })
                
                elif command == "leave_channel" and "channel" in data:
                    # Cancela a inscrição no canal
                    channel = data["channel"]
                    success = await channel_service.unsubscribe_from_channel(channel, user_id)
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "channel_unsubscription",
                        "channel": channel,
                        "success": success,
                        "message": f"{'Unsubscribed from' if success else 'Failed to unsubscribe from'} channel {channel}"
                    })
                
                elif command == "join_room" and "room" in data:
                    # Entra na sala
                    room = data["room"]
                    success = await channel_service.join_room(room, user_id)
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "room_joined",
                        "room": room,
                        "success": success,
                        "message": f"{'Joined' if success else 'Failed to join'} room {room}"
                    })
                
                elif command == "leave_room" and "room" in data:
                    # Sai da sala
                    room = data["room"]
                    success = await channel_service.leave_room(room, user_id)
                    
                    # Envia confirmação
                    await websocket.send_json({
                        "type": "room_left",
                        "room": room,
                        "success": success,
                        "message": f"{'Left' if success else 'Failed to leave'} room {room}"
                    })
                
                elif command == "get_subscriptions":
                    # Obtém as inscrições e salas do usuário
                    subscriptions = await channel_service.get_user_subscriptions(user_id)
                    rooms = await channel_service.get_user_rooms(user_id)
                    
                    # Envia as inscrições e salas
                    await websocket.send_json({
                        "type": "user_subscriptions",
                        "subscriptions": subscriptions,
                        "rooms": rooms
                    })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        import logging
        logging.error(f"WebSocket user error: {str(e)}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        websocket_manager.disconnect(websocket)