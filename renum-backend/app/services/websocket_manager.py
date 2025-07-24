"""
Gerenciador de conexões WebSocket para comunicação em tempo real.

Este módulo implementa o gerenciador de conexões WebSocket para comunicação
em tempo real entre o backend e o frontend, incluindo monitoramento de execuções,
notificações e atualizações de sistema.
"""

import logging
import json
import asyncio
from typing import Dict, Set, Any, Optional, List, Callable, Awaitable, Union
from uuid import UUID, uuid4
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import redis.asyncio as redis

from app.core.logger import logger
from app.models.websocket_models import (
    WebSocketConnection,
    WebSocketConnectionStatus,
    WebSocketNotification,
    WebSocketStats
)


class WebSocketManager:
    """Gerenciador de conexões WebSocket."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Inicializa o gerenciador de conexões WebSocket.
        
        Args:
            redis_client: Cliente Redis para PubSub (opcional)
        """
        # Dicionário de conexões ativas por canal
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Dicionário de conexões por usuário
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
        # Dicionário de metadados de conexão
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Mapeamento de WebSocket para connection_id
        self.websocket_to_connection_id: Dict[WebSocket, str] = {}
        
        # Cliente Redis para PubSub
        self.redis = redis_client
        
        # Prefixos de canais
        self.execution_channel_prefix = "ws:execution:"
        self.notification_channel_prefix = "ws:notification:"
        self.broadcast_channel = "ws:broadcast"
        self.user_channel_prefix = "ws:user:"
        
        # Tarefas de assinatura Redis PubSub
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        
        # Heartbeat
        self.heartbeat_interval = 30  # segundos
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
        
        # Tarefa de limpeza de conexões ociosas
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 60  # segundos
        self.idle_timeout = 30  # minutos
        
        # Repositório WebSocket (será definido posteriormente)
        self.repository = None
        
        logger.info("WebSocket Manager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        client_info: Optional[Dict[str, Any]] = None,
        resilience_service = None
    ):
        """
        Conecta um cliente WebSocket.
        
        Args:
            websocket: Conexão WebSocket
            user_id: ID do usuário
            client_info: Informações do cliente (opcional)
            resilience_service: Serviço de resiliência (opcional)
        """
        # Verifica limites de taxa se o serviço de resiliência estiver disponível
        if resilience_service:
            ip = client_info.get("ip", "unknown") if client_info else "unknown"
            rate_limit_result = await resilience_service.check_rate_limit(user_id, ip)
            
            if not rate_limit_result["allowed"]:
                # Rejeita a conexão se o limite de taxa foi excedido
                await websocket.close(code=1008, reason="Rate limit exceeded")
                
                logger.warning(
                    f"WebSocket connection rejected for user {user_id} due to rate limit: "
                    f"{rate_limit_result}"
                )
                return
        
        try:
            # Aceita a conexão
            await websocket.accept()
            
            # Gera um ID único para a conexão
            connection_id = str(uuid4())
            
            # Armazena metadados da conexão
            self.connection_metadata[websocket] = {
                "connection_id": connection_id,
                "user_id": user_id,
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "client_info": client_info or {},
                "subscribed_channels": []
            }
            
            # Mapeia WebSocket para connection_id
            self.websocket_to_connection_id[websocket] = connection_id
            
            # Adiciona à lista de conexões do usuário
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            
            self.user_connections[user_id].add(websocket)
            
            # Inicia heartbeat
            self.heartbeat_tasks[websocket] = asyncio.create_task(
                self._heartbeat_loop(websocket)
            )
            
            # Registra a conexão no repositório
            if self.repository:
                connection = WebSocketConnection(
                    connection_id=connection_id,
                    user_id=user_id,
                    status=WebSocketConnectionStatus.CONNECTED,
                    connected_at=datetime.now(),
                    last_activity=datetime.now(),
                    subscribed_channels=[],
                    client_info=client_info or {}
                )
                await self.repository.save_connection(connection)
            
            # Inicia a tarefa de limpeza se ainda não estiver em execução
            if self.repository and not self.cleanup_task:
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            # Envia mensagens armazenadas no buffer se o serviço de resiliência estiver disponível
            if resilience_service:
                buffered_messages = await resilience_service.get_buffered_messages(user_id)
                
                if buffered_messages:
                    logger.info(f"Sending {len(buffered_messages)} buffered messages to user {user_id}")
                    
                    for message in buffered_messages:
                        try:
                            await websocket.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending buffered message: {str(e)}")
                    
                    # Limpa as mensagens do buffer
                    await resilience_service.clear_buffered_messages(user_id)
                    
                # Registra sucesso no circuit breaker
                resilience_service.record_success(user_id)
            
            logger.info(f"WebSocket connection established for user {user_id} (connection_id: {connection_id})")
            
        except WebSocketDisconnect:
            # Registra falha no circuit breaker se o serviço de resiliência estiver disponível
            if resilience_service:
                resilience_service.record_failure(user_id)
            
            # Desconecta o WebSocket
            self.disconnect(websocket)
            
            logger.warning(f"WebSocket connection disconnected during setup for user {user_id}")
            
        except Exception as e:
            # Registra falha no circuit breaker se o serviço de resiliência estiver disponível
            if resilience_service:
                resilience_service.record_failure(user_id)
            
            # Desconecta o WebSocket
            if websocket.client_state.CONNECTED:
                await websocket.close(code=1011, reason=f"Error: {str(e)}")
            self.disconnect(websocket)
            
            logger.error(f"Error establishing WebSocket connection for user {user_id}: {str(e)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Desconecta um cliente WebSocket.
        
        Args:
            websocket: Conexão WebSocket
        """
        # Obtém metadados da conexão
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        user_id = metadata["user_id"]
        connection_id = metadata.get("connection_id")
        subscribed_channels = metadata.get("subscribed_channels", [])
        
        # Remove das listas de conexões por canal
        for channel in subscribed_channels:
            if channel in self.active_connections and websocket in self.active_connections[channel]:
                self.active_connections[channel].discard(websocket)
                
                # Se não houver mais conexões para este canal, remove a entrada
                if not self.active_connections[channel]:
                    self.active_connections.pop(channel)
                    
                    # Cancela a tarefa de assinatura PubSub
                    if channel in self.pubsub_tasks:
                        self.pubsub_tasks[channel].cancel()
                        self.pubsub_tasks.pop(channel)
        
        # Remove da lista de conexões do usuário
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            
            # Se não houver mais conexões para este usuário, remove a entrada
            if not self.user_connections[user_id]:
                self.user_connections.pop(user_id)
        
        # Cancela tarefa de heartbeat
        if websocket in self.heartbeat_tasks:
            self.heartbeat_tasks[websocket].cancel()
            self.heartbeat_tasks.pop(websocket)
        
        # Atualiza o repositório
        if self.repository and connection_id:
            asyncio.create_task(
                self.repository.update_connection(
                    connection_id,
                    {"status": WebSocketConnectionStatus.DISCONNECTED}
                )
            )
        
        # Remove metadados da conexão
        if websocket in self.connection_metadata:
            self.connection_metadata.pop(websocket)
        
        # Remove mapeamento de WebSocket para connection_id
        if websocket in self.websocket_to_connection_id:
            self.websocket_to_connection_id.pop(websocket)
        
        logger.info(f"WebSocket connection closed for user {user_id} (connection_id: {connection_id})")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """
        Inscreve um cliente em um canal.
        
        Args:
            websocket: Conexão WebSocket
            channel: Nome do canal
        """
        # Adiciona o canal à lista de canais inscritos
        if websocket in self.connection_metadata:
            if "subscribed_channels" not in self.connection_metadata[websocket]:
                self.connection_metadata[websocket]["subscribed_channels"] = []
            
            # Verifica se já está inscrito
            if channel in self.connection_metadata[websocket]["subscribed_channels"]:
                return
            
            self.connection_metadata[websocket]["subscribed_channels"].append(channel)
            
            # Atualiza o repositório
            if self.repository and websocket in self.websocket_to_connection_id:
                connection_id = self.websocket_to_connection_id[websocket]
                await self.repository.update_connection(
                    connection_id,
                    {"subscribed_channels": self.connection_metadata[websocket]["subscribed_channels"]}
                )
        
        # Adiciona a conexão à lista de conexões do canal
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
            
            # Se temos Redis, inscreve no canal PubSub
            if self.redis and channel not in self.pubsub_tasks:
                self.pubsub_tasks[channel] = asyncio.create_task(
                    self._subscribe_to_redis_channel(channel)
                )
        
        self.active_connections[channel].add(websocket)
        
        # Registra a atividade
        if self.repository and websocket in self.websocket_to_connection_id:
            connection_id = self.websocket_to_connection_id[websocket]
            await self.repository.log_message({
                "connection_id": connection_id,
                "event": "subscribe",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"WebSocket subscribed to channel {channel}")
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """
        Cancela a inscrição de um cliente em um canal.
        
        Args:
            websocket: Conexão WebSocket
            channel: Nome do canal
        """
        # Remove o canal da lista de canais inscritos
        if websocket in self.connection_metadata and "subscribed_channels" in self.connection_metadata[websocket]:
            if channel in self.connection_metadata[websocket]["subscribed_channels"]:
                self.connection_metadata[websocket]["subscribed_channels"].remove(channel)
                
                # Atualiza o repositório
                if self.repository and websocket in self.websocket_to_connection_id:
                    connection_id = self.websocket_to_connection_id[websocket]
                    await self.repository.update_connection(
                        connection_id,
                        {"subscribed_channels": self.connection_metadata[websocket]["subscribed_channels"]}
                    )
        
        # Remove a conexão da lista de conexões do canal
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            
            # Se não houver mais conexões para este canal, remove a entrada
            if not self.active_connections[channel]:
                self.active_connections.pop(channel)
                
                # Se temos Redis, cancela a inscrição no canal PubSub
                if self.redis and channel in self.pubsub_tasks:
                    self.pubsub_tasks[channel].cancel()
                    self.pubsub_tasks.pop(channel)
        
        # Registra a atividade
        if self.repository and websocket in self.websocket_to_connection_id:
            connection_id = self.websocket_to_connection_id[websocket]
            await self.repository.log_message({
                "connection_id": connection_id,
                "event": "unsubscribe",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"WebSocket unsubscribed from channel {channel}")
    
    async def send_personal_message(
        self,
        user_id: str,
        message: Dict[str, Any],
        resilience_service = None
    ):
        """
        Envia uma mensagem para um usuário específico.
        
        Args:
            user_id: ID do usuário
            message: Mensagem a ser enviada
            resilience_service: Serviço de resiliência (opcional)
        """
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Se o usuário não está conectado
        if user_id not in self.user_connections:
            # Armazena a mensagem no buffer se o serviço de resiliência estiver disponível
            if resilience_service:
                await resilience_service.buffer_message(user_id, message)
                logger.debug(f"Message buffered for offline user {user_id}")
            
            # Publica a mensagem no Redis
            if self.redis:
                channel = f"{self.user_channel_prefix}{user_id}"
                await self.redis.publish(channel, json.dumps(message))
            
            return
        
        # Converte a mensagem para JSON
        json_message = json.dumps(message)
        
        # Lista para armazenar conexões com erro
        disconnected_websockets = set()
        
        # Verifica se o circuit breaker permite enviar mensagens
        circuit_allowed = True
        if resilience_service:
            circuit_allowed = resilience_service.is_circuit_allowed(user_id)
        
        if not circuit_allowed:
            # Armazena a mensagem no buffer
            if resilience_service:
                await resilience_service.buffer_message(user_id, message)
                logger.debug(f"Message buffered for user {user_id} due to circuit breaker")
            return
        
        # Envia a mensagem para todas as conexões do usuário
        success = False
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(json_message)
                
                # Atualiza timestamp de última atividade
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_activity"] = datetime.now().isoformat()
                
                success = True
                
            except Exception as e:
                logger.error(f"Error sending personal WebSocket message: {str(e)}")
                disconnected_websockets.add(websocket)
        
        # Remove conexões com erro
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
        
        # Registra sucesso ou falha no circuit breaker
        if resilience_service:
            if success:
                resilience_service.record_success(user_id)
            else:
                resilience_service.record_failure(user_id)
                
                # Armazena a mensagem no buffer
                await resilience_service.buffer_message(user_id, message)
                logger.debug(f"Message buffered for user {user_id} due to delivery failure")
    
    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any],
        resilience_service = None
    ):
        """
        Envia uma mensagem para todos os clientes inscritos em um canal.
        
        Args:
            channel: Nome do canal
            message: Mensagem a ser enviada
            resilience_service: Serviço de resiliência (opcional)
        """
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Se temos Redis, publica a mensagem no canal
        if self.redis:
            await self.redis.publish(channel, json.dumps(message))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "channel": channel,
                "message": message,
                "timestamp": message["timestamp"]
            })
        
        if channel not in self.active_connections:
            return
        
        # Converte a mensagem para JSON
        json_message = json.dumps(message)
        
        # Lista para armazenar conexões com erro
        disconnected_websockets = set()
        
        # Mapeamento de usuários para status de entrega
        delivery_status: Dict[str, bool] = {}
        
        # Envia a mensagem para todos os clientes conectados ao canal
        for websocket in self.active_connections[channel]:
            try:
                # Obtém o user_id
                user_id = None
                if websocket in self.connection_metadata:
                    user_id = self.connection_metadata[websocket].get("user_id")
                
                # Verifica se o circuit breaker permite enviar mensagens
                circuit_allowed = True
                if resilience_service and user_id:
                    circuit_allowed = resilience_service.is_circuit_allowed(user_id)
                
                if not circuit_allowed:
                    # Armazena a mensagem no buffer
                    if resilience_service and user_id:
                        await resilience_service.buffer_message(user_id, message)
                        logger.debug(f"Channel message buffered for user {user_id} due to circuit breaker")
                    continue
                
                # Envia a mensagem
                await websocket.send_text(json_message)
                
                # Atualiza timestamp de última atividade
                now = datetime.now()
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_activity"] = now.isoformat()
                
                # Atualiza o repositório
                if self.repository and websocket in self.websocket_to_connection_id:
                    connection_id = self.websocket_to_connection_id[websocket]
                    await self.repository.update_connection(
                        connection_id,
                        {"last_activity": now}
                    )
                
                # Registra entrega bem-sucedida
                if user_id:
                    delivery_status[user_id] = True
                
            except Exception as e:
                logger.error(f"Error sending channel WebSocket message: {str(e)}")
                disconnected_websockets.add(websocket)
                
                # Registra falha na entrega
                if websocket in self.connection_metadata:
                    user_id = self.connection_metadata[websocket].get("user_id")
                    if user_id:
                        delivery_status[user_id] = False
        
        # Remove conexões com erro
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
        
        # Atualiza o circuit breaker e armazena mensagens não entregues
        if resilience_service:
            for user_id, success in delivery_status.items():
                if success:
                    resilience_service.record_success(user_id)
                else:
                    resilience_service.record_failure(user_id)
                    
                    # Armazena a mensagem no buffer
                    await resilience_service.buffer_message(user_id, message)
                    logger.debug(f"Channel message buffered for user {user_id} due to delivery failure")
    
    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        exclude_users: Optional[List[str]] = None,
        resilience_service = None
    ):
        """
        Envia uma mensagem para todos os clientes conectados.
        
        Args:
            message: Mensagem a ser enviada
            exclude_users: Lista de IDs de usuários a serem excluídos (opcional)
            resilience_service: Serviço de resiliência (opcional)
        """
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Se temos Redis, publica a mensagem no canal de broadcast
        if self.redis:
            message_with_exclude = message.copy()
            if exclude_users:
                message_with_exclude["exclude_users"] = exclude_users
            await self.redis.publish(self.broadcast_channel, json.dumps(message_with_exclude))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "broadcast": True,
                "message": message,
                "exclude_users": exclude_users,
                "timestamp": message["timestamp"]
            })
        
        # Converte a mensagem para JSON
        json_message = json.dumps(message)
        
        # Lista para armazenar conexões com erro
        disconnected_websockets = set()
        
        # Lista de usuários a excluir
        exclude_users = exclude_users or []
        
        # Mapeamento de usuários para status de entrega
        delivery_status: Dict[str, bool] = {}
        
        # Envia a mensagem para todos os usuários conectados
        for user_id, connections in self.user_connections.items():
            if user_id in exclude_users:
                continue
            
            # Verifica se o circuit breaker permite enviar mensagens
            circuit_allowed = True
            if resilience_service:
                circuit_allowed = resilience_service.is_circuit_allowed(user_id)
            
            if not circuit_allowed:
                # Armazena a mensagem no buffer
                if resilience_service:
                    await resilience_service.buffer_message(user_id, message)
                    logger.debug(f"Broadcast message buffered for user {user_id} due to circuit breaker")
                continue
            
            # Flag para verificar se pelo menos uma conexão recebeu a mensagem
            user_success = False
            
            for websocket in connections:
                try:
                    await websocket.send_text(json_message)
                    
                    # Atualiza timestamp de última atividade
                    now = datetime.now()
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket]["last_activity"] = now.isoformat()
                    
                    # Atualiza o repositório
                    if self.repository and websocket in self.websocket_to_connection_id:
                        connection_id = self.websocket_to_connection_id[websocket]
                        await self.repository.update_connection(
                            connection_id,
                            {"last_activity": now}
                        )
                    
                    user_success = True
                    
                except Exception as e:
                    logger.error(f"Error sending broadcast WebSocket message: {str(e)}")
                    disconnected_websockets.add(websocket)
            
            # Registra o status de entrega para o usuário
            delivery_status[user_id] = user_success
        
        # Remove conexões com erro
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
        
        # Atualiza o circuit breaker e armazena mensagens não entregues
        if resilience_service:
            for user_id, success in delivery_status.items():
                if success:
                    resilience_service.record_success(user_id)
                else:
                    resilience_service.record_failure(user_id)
                    
                    # Armazena a mensagem no buffer
                    await resilience_service.buffer_message(user_id, message)
                    logger.debug(f"Broadcast message buffered for user {user_id} due to delivery failure")
    
    async def broadcast_execution_update(self, execution_id: Union[UUID, str], message: Dict[str, Any]):
        """
        Envia uma atualização de execução para todos os clientes monitorando a execução.
        
        Args:
            execution_id: ID da execução
            message: Mensagem a ser enviada
        """
        execution_id_str = str(execution_id)
        channel = f"{self.execution_channel_prefix}{execution_id_str}"
        
        await self.broadcast_to_channel(channel, message)
    
    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """
        Envia uma notificação para um usuário específico.
        
        Args:
            user_id: ID do usuário
            notification: Dados da notificação
        """
        message = {
            "type": "notification",
            "data": notification
        }
        
        # Salva a notificação no repositório
        if self.repository:
            # Converte para o modelo de notificação
            notification_obj = WebSocketNotification(
                id=notification.get("id", str(uuid4())),
                user_id=user_id,
                type=notification.get("type", "info"),
                title=notification.get("title", ""),
                message=notification.get("message", ""),
                read=notification.get("read", False),
                created_at=datetime.now(),
                action=notification.get("action")
            )
            
            # Salva no repositório
            await self.repository.save_notification(notification_obj)
            
            # Atualiza a mensagem com o ID da notificação
            message["data"]["id"] = notification_obj.id
        
        # Envia a notificação pelo canal
        channel = f"{self.notification_channel_prefix}{user_id}"
        await self.broadcast_to_channel(channel, message)

    async def send_to_user(self, user_id: str, message: str):
        """
        Envia uma mensagem diretamente para um usuário (usado pelo serviço de notificações).
        
        Args:
            user_id: ID do usuário
            message: Mensagem em formato JSON string
        """
        try:
            message_dict = json.loads(message)
            await self.send_personal_message(user_id, message_dict)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message for user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
    
    async def _subscribe_to_redis_channel(self, channel: str):
        """
        Inscreve-se em um canal Redis PubSub e encaminha mensagens para os clientes WebSocket.
        
        Args:
            channel: Nome do canal
        """
        if not self.redis:
            return
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"Subscribed to Redis channel: {channel}")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        
                        # Se a mensagem contém exclude_users, filtra os usuários
                        exclude_users = data.pop("exclude_users", []) if isinstance(data, dict) else []
                        
                        # Encaminha a mensagem para os clientes WebSocket
                        if channel == self.broadcast_channel:
                            await self.broadcast_to_all(data, exclude_users)
                        else:
                            await self.broadcast_to_channel(channel, data)
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {str(e)}")
                
                await asyncio.sleep(0.01)  # Evita consumo excessivo de CPU
                
        except asyncio.CancelledError:
            logger.info(f"Unsubscribed from Redis channel: {channel}")
            await pubsub.unsubscribe(channel)
        except Exception as e:
            logger.error(f"Error in Redis subscription: {str(e)}")
    
    async def _heartbeat_loop(self, websocket: WebSocket):
        """
        Envia heartbeats periódicos para manter a conexão ativa.
        
        Args:
            websocket: Conexão WebSocket
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                
                try:
                    # Verifica se a conexão ainda está ativa
                    if websocket not in self.connection_metadata:
                        break
                    
                    # Envia heartbeat
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Atualiza timestamp de última atividade
                    now = datetime.now()
                    self.connection_metadata[websocket]["last_activity"] = now.isoformat()
                    
                    # Atualiza o repositório
                    if self.repository and websocket in self.websocket_to_connection_id:
                        connection_id = self.websocket_to_connection_id[websocket]
                        await self.repository.update_connection(
                            connection_id,
                            {"last_activity": now}
                        )
                    
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {str(e)}")
                    self.disconnect(websocket)
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {str(e)}")
            self.disconnect(websocket)
    
    async def _cleanup_loop(self):
        """
        Limpa periodicamente conexões ociosas.
        """
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                
                try:
                    if self.repository:
                        # Limpa conexões ociosas no repositório
                        cleaned_count = await self.repository.clean_idle_connections(self.idle_timeout)
                        if cleaned_count > 0:
                            logger.info(f"Cleaned {cleaned_count} idle WebSocket connections")
                
                except Exception as e:
                    logger.error(f"Error in cleanup loop: {str(e)}")
                    
        except asyncio.CancelledError:
            logger.info("WebSocket cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in cleanup loop: {str(e)}")
            
    def set_repository(self, repository):
        """
        Define o repositório WebSocket.
        
        Args:
            repository: Repositório WebSocket
        """
        self.repository = repository
    
    def get_active_connections_count(self) -> int:
        """
        Retorna o número total de conexões ativas.
        
        Returns:
            Número de conexões ativas
        """
        return len(self.connection_metadata)
    
    def get_active_users_count(self) -> int:
        """
        Retorna o número de usuários conectados.
        
        Returns:
            Número de usuários conectados
        """
        return len(self.user_connections)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre as conexões ativas.
        
        Returns:
            Dicionário com estatísticas
        """
        # Se temos repositório, usa as estatísticas dele
        if self.repository:
            stats = await self.repository.get_stats()
            return stats.dict()
        
        # Caso contrário, usa as estatísticas em memória
        return {
            "total_connections": self.get_active_connections_count(),
            "active_users": self.get_active_users_count(),
            "channels": {
                channel: len(connections)
                for channel, connections in self.active_connections.items()
            },
            "connection_rate": 0,
            "message_rate": 0,
            "uptime": 0
        }


# Instância global do gerenciador de WebSockets
websocket_manager = WebSocketManager()