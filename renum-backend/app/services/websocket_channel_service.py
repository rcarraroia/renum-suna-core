"""
Serviço para gerenciamento de canais e salas WebSocket.

Este módulo implementa o serviço para gerenciamento de canais e salas WebSocket,
permitindo a criação, inscrição e publicação em canais e salas.
"""

import logging
import json
import asyncio
from typing import Dict, Set, List, Any, Optional, Union
from datetime import datetime
import redis.asyncio as redis
from uuid import UUID, uuid4

from app.core.logger import logger
from app.models.websocket_models import WebSocketMessage, WebSocketMessageType
from app.repositories.websocket_repository import WebSocketRepository


class WebSocketChannelService:
    """Serviço para gerenciamento de canais e salas WebSocket."""
    
    def __init__(self, redis_client: redis.Redis, repository: Optional[WebSocketRepository] = None):
        """
        Inicializa o serviço.
        
        Args:
            redis_client: Cliente Redis para PubSub
            repository: Repositório WebSocket (opcional)
        """
        self.redis = redis_client
        self.repository = repository
        
        # Prefixos de canais
        self.channel_prefix = "ws:channel:"
        self.room_prefix = "ws:room:"
        self.user_prefix = "ws:user:"
        self.broadcast_channel = "ws:broadcast"
        
        # Canais com permissões especiais
        self.protected_channels = set([
            "admin",
            "system",
            "notifications"
        ])
        
        # Mapeamento de canais para assinantes
        self.channel_subscribers: Dict[str, Set[str]] = {}
        
        # Mapeamento de salas para membros
        self.room_members: Dict[str, Set[str]] = {}
        
        # Tarefas de assinatura Redis PubSub
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        
        # Handlers de mensagens por tipo
        self.message_handlers: Dict[str, List[callable]] = {}
        
        logger.info("WebSocket Channel Service initialized")
    
    async def create_channel(self, channel_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Cria um novo canal.
        
        Args:
            channel_name: Nome do canal
            metadata: Metadados do canal (opcional)
            
        Returns:
            Nome completo do canal
        """
        full_channel = f"{self.channel_prefix}{channel_name}"
        
        # Armazena metadados do canal no Redis
        if metadata:
            await self.redis.hset(
                f"{full_channel}:metadata",
                mapping={
                    "name": channel_name,
                    "created_at": datetime.now().isoformat(),
                    "metadata": json.dumps(metadata)
                }
            )
        
        # Inicia a assinatura no canal Redis PubSub
        if full_channel not in self.pubsub_tasks:
            self.pubsub_tasks[full_channel] = asyncio.create_task(
                self._subscribe_to_redis_channel(full_channel)
            )
        
        # Inicializa o conjunto de assinantes
        if full_channel not in self.channel_subscribers:
            self.channel_subscribers[full_channel] = set()
        
        logger.info(f"Created WebSocket channel: {channel_name}")
        return full_channel
    
    async def create_room(self, room_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Cria uma nova sala.
        
        Args:
            room_name: Nome da sala
            metadata: Metadados da sala (opcional)
            
        Returns:
            Nome completo da sala
        """
        full_room = f"{self.room_prefix}{room_name}"
        
        # Armazena metadados da sala no Redis
        if metadata:
            await self.redis.hset(
                f"{full_room}:metadata",
                mapping={
                    "name": room_name,
                    "created_at": datetime.now().isoformat(),
                    "metadata": json.dumps(metadata)
                }
            )
        
        # Inicia a assinatura no canal Redis PubSub
        if full_room not in self.pubsub_tasks:
            self.pubsub_tasks[full_room] = asyncio.create_task(
                self._subscribe_to_redis_channel(full_room)
            )
        
        # Inicializa o conjunto de membros
        if full_room not in self.room_members:
            self.room_members[full_room] = set()
        
        logger.info(f"Created WebSocket room: {room_name}")
        return full_room
    
    async def subscribe_to_channel(self, channel_name: str, user_id: str) -> bool:
        """
        Inscreve um usuário em um canal.
        
        Args:
            channel_name: Nome do canal
            user_id: ID do usuário
            
        Returns:
            True se a inscrição foi bem-sucedida, False caso contrário
        """
        # Verifica se o canal é protegido
        if channel_name in self.protected_channels:
            # TODO: Implementar verificação de permissões
            logger.warning(f"User {user_id} attempted to subscribe to protected channel {channel_name}")
            return False
        
        full_channel = f"{self.channel_prefix}{channel_name}"
        
        # Cria o canal se não existir
        if full_channel not in self.channel_subscribers:
            await self.create_channel(channel_name)
        
        # Adiciona o usuário à lista de assinantes
        self.channel_subscribers[full_channel].add(user_id)
        
        # Armazena a inscrição no Redis
        await self.redis.sadd(f"{full_channel}:subscribers", user_id)
        await self.redis.sadd(f"{self.user_prefix}{user_id}:subscriptions", full_channel)
        
        logger.info(f"User {user_id} subscribed to channel {channel_name}")
        return True
    
    async def unsubscribe_from_channel(self, channel_name: str, user_id: str) -> bool:
        """
        Cancela a inscrição de um usuário em um canal.
        
        Args:
            channel_name: Nome do canal
            user_id: ID do usuário
            
        Returns:
            True se o cancelamento foi bem-sucedido, False caso contrário
        """
        full_channel = f"{self.channel_prefix}{channel_name}"
        
        # Verifica se o canal existe
        if full_channel not in self.channel_subscribers:
            return False
        
        # Remove o usuário da lista de assinantes
        self.channel_subscribers[full_channel].discard(user_id)
        
        # Remove a inscrição do Redis
        await self.redis.srem(f"{full_channel}:subscribers", user_id)
        await self.redis.srem(f"{self.user_prefix}{user_id}:subscriptions", full_channel)
        
        # Se não houver mais assinantes, cancela a assinatura PubSub
        if not self.channel_subscribers[full_channel] and full_channel in self.pubsub_tasks:
            self.pubsub_tasks[full_channel].cancel()
            self.pubsub_tasks.pop(full_channel)
            self.channel_subscribers.pop(full_channel)
        
        logger.info(f"User {user_id} unsubscribed from channel {channel_name}")
        return True
    
    async def join_room(self, room_name: str, user_id: str) -> bool:
        """
        Adiciona um usuário a uma sala.
        
        Args:
            room_name: Nome da sala
            user_id: ID do usuário
            
        Returns:
            True se a adição foi bem-sucedida, False caso contrário
        """
        full_room = f"{self.room_prefix}{room_name}"
        
        # Cria a sala se não existir
        if full_room not in self.room_members:
            await self.create_room(room_name)
        
        # Adiciona o usuário à lista de membros
        self.room_members[full_room].add(user_id)
        
        # Armazena a associação no Redis
        await self.redis.sadd(f"{full_room}:members", user_id)
        await self.redis.sadd(f"{self.user_prefix}{user_id}:rooms", full_room)
        
        # Publica evento de entrada na sala
        await self.publish_to_room(
            room_name,
            {
                "type": "room_event",
                "event": "join",
                "user_id": user_id,
                "room": room_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"User {user_id} joined room {room_name}")
        return True
    
    async def leave_room(self, room_name: str, user_id: str) -> bool:
        """
        Remove um usuário de uma sala.
        
        Args:
            room_name: Nome da sala
            user_id: ID do usuário
            
        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        full_room = f"{self.room_prefix}{room_name}"
        
        # Verifica se a sala existe
        if full_room not in self.room_members:
            return False
        
        # Publica evento de saída da sala
        await self.publish_to_room(
            room_name,
            {
                "type": "room_event",
                "event": "leave",
                "user_id": user_id,
                "room": room_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Remove o usuário da lista de membros
        self.room_members[full_room].discard(user_id)
        
        # Remove a associação do Redis
        await self.redis.srem(f"{full_room}:members", user_id)
        await self.redis.srem(f"{self.user_prefix}{user_id}:rooms", full_room)
        
        # Se não houver mais membros, cancela a assinatura PubSub
        if not self.room_members[full_room] and full_room in self.pubsub_tasks:
            self.pubsub_tasks[full_room].cancel()
            self.pubsub_tasks.pop(full_room)
            self.room_members.pop(full_room)
        
        logger.info(f"User {user_id} left room {room_name}")
        return True
    
    async def publish_to_channel(self, channel_name: str, message: Dict[str, Any]) -> bool:
        """
        Publica uma mensagem em um canal.
        
        Args:
            channel_name: Nome do canal
            message: Mensagem a ser publicada
            
        Returns:
            True se a publicação foi bem-sucedida, False caso contrário
        """
        full_channel = f"{self.channel_prefix}{channel_name}"
        
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Publica a mensagem no Redis
        await self.redis.publish(full_channel, json.dumps(message))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "channel": channel_name,
                "message": message,
                "timestamp": message["timestamp"]
            })
        
        logger.debug(f"Published message to channel {channel_name}")
        return True
    
    async def publish_to_room(self, room_name: str, message: Dict[str, Any]) -> bool:
        """
        Publica uma mensagem em uma sala.
        
        Args:
            room_name: Nome da sala
            message: Mensagem a ser publicada
            
        Returns:
            True se a publicação foi bem-sucedida, False caso contrário
        """
        full_room = f"{self.room_prefix}{room_name}"
        
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Publica a mensagem no Redis
        await self.redis.publish(full_room, json.dumps(message))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "room": room_name,
                "message": message,
                "timestamp": message["timestamp"]
            })
        
        logger.debug(f"Published message to room {room_name}")
        return True
    
    async def publish_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """
        Publica uma mensagem para um usuário específico.
        
        Args:
            user_id: ID do usuário
            message: Mensagem a ser publicada
            
        Returns:
            True se a publicação foi bem-sucedida, False caso contrário
        """
        user_channel = f"{self.user_prefix}{user_id}"
        
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Publica a mensagem no Redis
        await self.redis.publish(user_channel, json.dumps(message))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "user_id": user_id,
                "message": message,
                "timestamp": message["timestamp"]
            })
        
        logger.debug(f"Published message to user {user_id}")
        return True
    
    async def broadcast(self, message: Dict[str, Any], exclude_users: Optional[List[str]] = None) -> bool:
        """
        Publica uma mensagem para todos os usuários.
        
        Args:
            message: Mensagem a ser publicada
            exclude_users: Lista de IDs de usuários a serem excluídos (opcional)
            
        Returns:
            True se a publicação foi bem-sucedida, False caso contrário
        """
        # Adiciona timestamp à mensagem
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Adiciona lista de exclusão à mensagem
        broadcast_message = message.copy()
        if exclude_users:
            broadcast_message["exclude_users"] = exclude_users
        
        # Publica a mensagem no Redis
        await self.redis.publish(self.broadcast_channel, json.dumps(broadcast_message))
        
        # Registra a mensagem no repositório
        if self.repository:
            await self.repository.log_message({
                "broadcast": True,
                "message": message,
                "exclude_users": exclude_users,
                "timestamp": message["timestamp"]
            })
        
        logger.debug("Published broadcast message")
        return True
    
    async def get_channel_subscribers(self, channel_name: str) -> List[str]:
        """
        Obtém os assinantes de um canal.
        
        Args:
            channel_name: Nome do canal
            
        Returns:
            Lista de IDs de usuários inscritos no canal
        """
        full_channel = f"{self.channel_prefix}{channel_name}"
        
        # Obtém os assinantes do Redis
        subscribers = await self.redis.smembers(f"{full_channel}:subscribers")
        
        # Converte para strings
        return [sub.decode("utf-8") for sub in subscribers]
    
    async def get_room_members(self, room_name: str) -> List[str]:
        """
        Obtém os membros de uma sala.
        
        Args:
            room_name: Nome da sala
            
        Returns:
            Lista de IDs de usuários na sala
        """
        full_room = f"{self.room_prefix}{room_name}"
        
        # Obtém os membros do Redis
        members = await self.redis.smembers(f"{full_room}:members")
        
        # Converte para strings
        return [member.decode("utf-8") for member in members]
    
    async def get_user_subscriptions(self, user_id: str) -> List[str]:
        """
        Obtém as inscrições de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de canais inscritos pelo usuário
        """
        # Obtém as inscrições do Redis
        subscriptions = await self.redis.smembers(f"{self.user_prefix}{user_id}:subscriptions")
        
        # Converte para strings e remove o prefixo
        return [
            sub.decode("utf-8").replace(self.channel_prefix, "")
            for sub in subscriptions
        ]
    
    async def get_user_rooms(self, user_id: str) -> List[str]:
        """
        Obtém as salas de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de salas do usuário
        """
        # Obtém as salas do Redis
        rooms = await self.redis.smembers(f"{self.user_prefix}{user_id}:rooms")
        
        # Converte para strings e remove o prefixo
        return [
            room.decode("utf-8").replace(self.room_prefix, "")
            for room in rooms
        ]
    
    def register_message_handler(self, message_type: str, handler: callable) -> None:
        """
        Registra um handler para um tipo de mensagem.
        
        Args:
            message_type: Tipo de mensagem
            handler: Função de tratamento
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def _subscribe_to_redis_channel(self, channel: str) -> None:
        """
        Inscreve-se em um canal Redis PubSub e processa mensagens.
        
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
                        
                        # Processa a mensagem com os handlers registrados
                        if isinstance(data, dict) and "type" in data:
                            message_type = data["type"]
                            if message_type in self.message_handlers:
                                for handler in self.message_handlers[message_type]:
                                    try:
                                        await handler(data)
                                    except Exception as e:
                                        logger.error(f"Error in message handler: {str(e)}")
                        
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


# Instância global do serviço de canais WebSocket
websocket_channel_service = WebSocketChannelService(None)