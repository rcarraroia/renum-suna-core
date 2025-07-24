"""
Repositório para WebSocket.

Este módulo implementa o repositório para armazenar e recuperar informações
sobre conexões WebSocket, incluindo estatísticas e logs.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import redis.asyncio as redis
from uuid import uuid4

from app.models.websocket_models import (
    WebSocketConnection,
    WebSocketNotification,
    WebSocketStats,
    WebSocketConnectionStatus
)

logger = logging.getLogger(__name__)


class WebSocketRepository:
    """Repositório para WebSocket."""
    
    def __init__(self, redis_client: redis.Redis):
        """
        Inicializa o repositório.
        
        Args:
            redis_client: Cliente Redis
        """
        self.redis = redis_client
        self.connection_key_prefix = "ws:connection:"
        self.notification_key_prefix = "ws:notification:"
        self.stats_key = "ws:stats"
        self.connection_log_key = "ws:connection_log"
        self.message_log_key = "ws:message_log"
        self.active_connections_key = "ws:active_connections"
        self.active_users_key = "ws:active_users"
        self.start_time = datetime.now()
    
    async def save_connection(self, connection: WebSocketConnection) -> str:
        """
        Salva uma conexão WebSocket.
        
        Args:
            connection: Conexão WebSocket
            
        Returns:
            ID da conexão
        """
        # Gera um ID se não existir
        if not connection.connection_id:
            connection.connection_id = str(uuid4())
        
        # Salva a conexão no Redis
        connection_key = f"{self.connection_key_prefix}{connection.connection_id}"
        await self.redis.hset(
            connection_key,
            mapping={
                "user_id": connection.user_id,
                "status": connection.status,
                "connected_at": connection.connected_at.isoformat(),
                "last_activity": connection.last_activity.isoformat(),
                "subscribed_channels": json.dumps(connection.subscribed_channels),
                "client_info": json.dumps(connection.client_info)
            }
        )
        
        # Define TTL (24 horas)
        await self.redis.expire(connection_key, 86400)
        
        # Adiciona à lista de conexões ativas
        if connection.status == WebSocketConnectionStatus.CONNECTED:
            await self.redis.sadd(self.active_connections_key, connection.connection_id)
            await self.redis.sadd(f"{self.active_users_key}:{connection.user_id}", connection.connection_id)
        
        # Registra no log de conexões
        await self.redis.lpush(
            self.connection_log_key,
            json.dumps({
                "connection_id": connection.connection_id,
                "user_id": connection.user_id,
                "event": "connect",
                "timestamp": datetime.now().isoformat(),
                "client_info": connection.client_info
            })
        )
        
        # Limita o tamanho do log
        await self.redis.ltrim(self.connection_log_key, 0, 999)
        
        # Atualiza estatísticas
        await self._update_connection_stats()
        
        return connection.connection_id
    
    async def update_connection(self, connection_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza uma conexão WebSocket.
        
        Args:
            connection_id: ID da conexão
            updates: Atualizações a serem aplicadas
            
        Returns:
            True se a conexão foi atualizada, False caso contrário
        """
        connection_key = f"{self.connection_key_prefix}{connection_id}"
        
        # Verifica se a conexão existe
        if not await self.redis.exists(connection_key):
            return False
        
        # Prepara as atualizações
        mapping = {}
        
        if "status" in updates:
            mapping["status"] = updates["status"]
            
            # Atualiza listas de conexões ativas
            if updates["status"] == WebSocketConnectionStatus.CONNECTED:
                await self.redis.sadd(self.active_connections_key, connection_id)
            else:
                await self.redis.srem(self.active_connections_key, connection_id)
        
        if "last_activity" in updates:
            mapping["last_activity"] = updates["last_activity"].isoformat()
        
        if "subscribed_channels" in updates:
            mapping["subscribed_channels"] = json.dumps(updates["subscribed_channels"])
        
        if "client_info" in updates:
            # Obtém as informações atuais do cliente
            current_client_info = json.loads(await self.redis.hget(connection_key, "client_info") or "{}")
            # Atualiza com as novas informações
            current_client_info.update(updates["client_info"])
            mapping["client_info"] = json.dumps(current_client_info)
        
        # Aplica as atualizações
        if mapping:
            await self.redis.hset(connection_key, mapping=mapping)
            return True
        
        return False
    
    async def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """
        Obtém uma conexão WebSocket.
        
        Args:
            connection_id: ID da conexão
            
        Returns:
            Conexão WebSocket ou None se não existir
        """
        connection_key = f"{self.connection_key_prefix}{connection_id}"
        
        # Verifica se a conexão existe
        if not await self.redis.exists(connection_key):
            return None
        
        # Obtém os dados da conexão
        data = await self.redis.hgetall(connection_key)
        
        if not data:
            return None
        
        # Converte os dados para o modelo
        return WebSocketConnection(
            connection_id=connection_id,
            user_id=data.get(b"user_id", b"").decode("utf-8"),
            status=data.get(b"status", b"connected").decode("utf-8"),
            connected_at=datetime.fromisoformat(data.get(b"connected_at", datetime.now().isoformat()).decode("utf-8")),
            last_activity=datetime.fromisoformat(data.get(b"last_activity", datetime.now().isoformat()).decode("utf-8")),
            subscribed_channels=json.loads(data.get(b"subscribed_channels", b"[]").decode("utf-8")),
            client_info=json.loads(data.get(b"client_info", b"{}").decode("utf-8"))
        )
    
    async def delete_connection(self, connection_id: str) -> bool:
        """
        Exclui uma conexão WebSocket.
        
        Args:
            connection_id: ID da conexão
            
        Returns:
            True se a conexão foi excluída, False caso contrário
        """
        connection_key = f"{self.connection_key_prefix}{connection_id}"
        
        # Verifica se a conexão existe
        if not await self.redis.exists(connection_key):
            return False
        
        # Obtém o user_id antes de excluir
        user_id = await self.redis.hget(connection_key, "user_id")
        user_id = user_id.decode("utf-8") if user_id else None
        
        # Registra no log de conexões
        if user_id:
            await self.redis.lpush(
                self.connection_log_key,
                json.dumps({
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "event": "disconnect",
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            # Remove da lista de conexões do usuário
            await self.redis.srem(f"{self.active_users_key}:{user_id}", connection_id)
        
        # Remove da lista de conexões ativas
        await self.redis.srem(self.active_connections_key, connection_id)
        
        # Exclui a conexão
        await self.redis.delete(connection_key)
        
        # Atualiza estatísticas
        await self._update_connection_stats()
        
        return True
    
    async def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """
        Obtém as conexões de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de conexões do usuário
        """
        # Obtém os IDs das conexões do usuário
        connection_ids = await self.redis.smembers(f"{self.active_users_key}:{user_id}")
        
        # Converte para strings
        connection_ids = [conn_id.decode("utf-8") for conn_id in connection_ids]
        
        # Obtém as conexões
        connections = []
        for connection_id in connection_ids:
            connection = await self.get_connection(connection_id)
            if connection:
                connections.append(connection)
        
        return connections
    
    async def get_channel_connections(self, channel: str) -> List[WebSocketConnection]:
        """
        Obtém as conexões inscritas em um canal.
        
        Args:
            channel: Nome do canal
            
        Returns:
            Lista de conexões inscritas no canal
        """
        # Obtém todas as conexões ativas
        connection_ids = await self.redis.smembers(self.active_connections_key)
        
        # Converte para strings
        connection_ids = [conn_id.decode("utf-8") for conn_id in connection_ids]
        
        # Filtra as conexões inscritas no canal
        connections = []
        for connection_id in connection_ids:
            connection = await self.get_connection(connection_id)
            if connection and channel in connection.subscribed_channels:
                connections.append(connection)
        
        return connections
    
    async def save_notification(self, notification: WebSocketNotification) -> str:
        """
        Salva uma notificação.
        
        Args:
            notification: Notificação
            
        Returns:
            ID da notificação
        """
        # Gera um ID se não existir
        if not notification.id:
            notification.id = str(uuid4())
        
        # Salva a notificação no Redis
        notification_key = f"{self.notification_key_prefix}{notification.user_id}:{notification.id}"
        await self.redis.hset(
            notification_key,
            mapping={
                "id": notification.id,
                "user_id": notification.user_id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "read": json.dumps(notification.read),
                "created_at": notification.created_at.isoformat(),
                "action": json.dumps(notification.action) if notification.action else ""
            }
        )
        
        # Define TTL (30 dias)
        await self.redis.expire(notification_key, 30 * 86400)
        
        # Adiciona à lista de notificações do usuário
        await self.redis.zadd(
            f"{self.notification_key_prefix}{notification.user_id}",
            {notification.id: notification.created_at.timestamp()}
        )
        
        return notification.id
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[WebSocketNotification]:
        """
        Obtém as notificações de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de resultados
            offset: Deslocamento para paginação
            unread_only: Se True, retorna apenas notificações não lidas
            
        Returns:
            Lista de notificações do usuário
        """
        # Obtém os IDs das notificações do usuário
        notification_ids = await self.redis.zrevrange(
            f"{self.notification_key_prefix}{user_id}",
            offset,
            offset + limit - 1
        )
        
        # Converte para strings
        notification_ids = [notif_id.decode("utf-8") for notif_id in notification_ids]
        
        # Obtém as notificações
        notifications = []
        for notification_id in notification_ids:
            notification_key = f"{self.notification_key_prefix}{user_id}:{notification_id}"
            data = await self.redis.hgetall(notification_key)
            
            if not data:
                continue
            
            # Converte os dados para o modelo
            read = json.loads(data.get(b"read", b"false").decode("utf-8"))
            
            # Filtra por status de leitura
            if unread_only and read:
                continue
            
            action_str = data.get(b"action", b"").decode("utf-8")
            action = json.loads(action_str) if action_str else None
            
            notification = WebSocketNotification(
                id=notification_id,
                user_id=user_id,
                type=data.get(b"type", b"").decode("utf-8"),
                title=data.get(b"title", b"").decode("utf-8"),
                message=data.get(b"message", b"").decode("utf-8"),
                read=read,
                created_at=datetime.fromisoformat(data.get(b"created_at", datetime.now().isoformat()).decode("utf-8")),
                action=action
            )
            
            notifications.append(notification)
        
        return notifications
    
    async def mark_notification_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        Marca uma notificação como lida.
        
        Args:
            user_id: ID do usuário
            notification_id: ID da notificação
            
        Returns:
            True se a notificação foi marcada como lida, False caso contrário
        """
        notification_key = f"{self.notification_key_prefix}{user_id}:{notification_id}"
        
        # Verifica se a notificação existe
        if not await self.redis.exists(notification_key):
            return False
        
        # Marca como lida
        await self.redis.hset(notification_key, "read", "true")
        
        return True
    
    async def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        Exclui uma notificação.
        
        Args:
            user_id: ID do usuário
            notification_id: ID da notificação
            
        Returns:
            True se a notificação foi excluída, False caso contrário
        """
        notification_key = f"{self.notification_key_prefix}{user_id}:{notification_id}"
        
        # Verifica se a notificação existe
        if not await self.redis.exists(notification_key):
            return False
        
        # Remove da lista de notificações do usuário
        await self.redis.zrem(f"{self.notification_key_prefix}{user_id}", notification_id)
        
        # Exclui a notificação
        await self.redis.delete(notification_key)
        
        return True
    
    async def get_stats(self) -> WebSocketStats:
        """
        Obtém estatísticas de WebSocket.
        
        Returns:
            Estatísticas de WebSocket
        """
        # Obtém o número de conexões ativas
        total_connections = await self.redis.scard(self.active_connections_key)
        
        # Obtém o número de usuários ativos
        active_users_keys = await self.redis.keys(f"{self.active_users_key}:*")
        active_users = len(active_users_keys)
        
        # Obtém o número de conexões por canal
        channels = {}
        connection_ids = await self.redis.smembers(self.active_connections_key)
        connection_ids = [conn_id.decode("utf-8") for conn_id in connection_ids]
        
        for connection_id in connection_ids:
            connection = await self.get_connection(connection_id)
            if connection:
                for channel in connection.subscribed_channels:
                    channels[channel] = channels.get(channel, 0) + 1
        
        # Calcula a taxa de conexões por minuto
        connection_logs = await self.redis.lrange(self.connection_log_key, 0, 99)
        recent_connections = 0
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        
        for log_entry in connection_logs:
            entry = json.loads(log_entry)
            if entry["event"] == "connect" and datetime.fromisoformat(entry["timestamp"]) > one_minute_ago:
                recent_connections += 1
        
        connection_rate = recent_connections / 1.0  # por minuto
        
        # Calcula a taxa de mensagens por minuto
        message_logs = await self.redis.lrange(self.message_log_key, 0, 99)
        recent_messages = 0
        
        for log_entry in message_logs:
            entry = json.loads(log_entry)
            if datetime.fromisoformat(entry["timestamp"]) > one_minute_ago:
                recent_messages += 1
        
        message_rate = recent_messages / 1.0  # por minuto
        
        # Calcula o tempo de atividade
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return WebSocketStats(
            total_connections=total_connections,
            active_users=active_users,
            channels=channels,
            connection_rate=connection_rate,
            message_rate=message_rate,
            uptime=uptime
        )
    
    async def log_message(self, message_data: Dict[str, Any]) -> None:
        """
        Registra uma mensagem no log.
        
        Args:
            message_data: Dados da mensagem
        """
        # Adiciona timestamp se não existir
        if "timestamp" not in message_data:
            message_data["timestamp"] = datetime.now().isoformat()
        
        # Registra no log de mensagens
        await self.redis.lpush(self.message_log_key, json.dumps(message_data))
        
        # Limita o tamanho do log
        await self.redis.ltrim(self.message_log_key, 0, 999)
    
    async def clean_idle_connections(self, idle_timeout: int = 30) -> int:
        """
        Limpa conexões ociosas.
        
        Args:
            idle_timeout: Tempo limite de inatividade em minutos
            
        Returns:
            Número de conexões limpas
        """
        # Obtém todas as conexões ativas
        connection_ids = await self.redis.smembers(self.active_connections_key)
        connection_ids = [conn_id.decode("utf-8") for conn_id in connection_ids]
        
        # Verifica cada conexão
        cleaned_count = 0
        idle_threshold = datetime.now() - timedelta(minutes=idle_timeout)
        
        for connection_id in connection_ids:
            connection = await self.get_connection(connection_id)
            if connection and connection.last_activity < idle_threshold:
                # Marca como desconectada
                await self.update_connection(
                    connection_id,
                    {"status": WebSocketConnectionStatus.DISCONNECTED}
                )
                
                # Remove da lista de conexões ativas
                await self.redis.srem(self.active_connections_key, connection_id)
                
                # Remove da lista de conexões do usuário
                await self.redis.srem(
                    f"{self.active_users_key}:{connection.user_id}",
                    connection_id
                )
                
                cleaned_count += 1
        
        # Atualiza estatísticas
        if cleaned_count > 0:
            await self._update_connection_stats()
        
        return cleaned_count
    
    async def _update_connection_stats(self) -> None:
        """Atualiza as estatísticas de conexão."""
        # Obtém o número de conexões ativas
        total_connections = await self.redis.scard(self.active_connections_key)
        
        # Obtém o número de usuários ativos
        active_users_keys = await self.redis.keys(f"{self.active_users_key}:*")
        active_users = len(active_users_keys)
        
        # Atualiza as estatísticas
        await self.redis.hset(
            self.stats_key,
            mapping={
                "total_connections": total_connections,
                "active_users": active_users,
                "last_updated": datetime.now().isoformat()
            }
        )