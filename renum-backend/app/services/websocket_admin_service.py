"""
Serviço administrativo para gerenciamento de conexões WebSocket
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from app.services.websocket_manager import WebSocketManager
from app.repositories.websocket_repository import WebSocketRepository

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Informações de uma conexão WebSocket"""
    connection_id: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    connected_at: datetime
    last_activity: datetime
    channels: List[str]
    message_count: int
    bytes_sent: int
    bytes_received: int
    status: str  # 'active', 'idle', 'disconnected'
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        data['connected_at'] = self.connected_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data

@dataclass
class ConnectionStats:
    """Estatísticas de conexões"""
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
    peak_connections_time: Optional[datetime]

class WebSocketAdminService:
    """Serviço administrativo para WebSocket"""
    
    def __init__(
        self, 
        websocket_manager: WebSocketManager,
        websocket_repository: WebSocketRepository
    ):
        self.websocket_manager = websocket_manager
        self.websocket_repository = websocket_repository
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.stats_history: List[ConnectionStats] = []
        self.idle_threshold_minutes = 5
        self.max_history_entries = 1440  # 24 horas com coleta a cada minuto

    async def get_active_connections(
        self, 
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ConnectionInfo]:
        """Obtém lista de conexões ativas"""
        connections = list(self.connection_info.values())
        
        # Filtrar por usuário se especificado
        if user_id:
            connections = [conn for conn in connections if conn.user_id == user_id]
        
        # Ordenar por última atividade (mais recente primeiro)
        connections.sort(key=lambda x: x.last_activity, reverse=True)
        
        # Aplicar paginação
        if limit:
            connections = connections[offset:offset + limit]
        
        return connections

    async def get_connection_by_id(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Obtém informações de uma conexão específica"""
        return self.connection_info.get(connection_id)

    async def get_connections_by_user(self, user_id: str) -> List[ConnectionInfo]:
        """Obtém todas as conexões de um usuário"""
        return [
            conn for conn in self.connection_info.values() 
            if conn.user_id == user_id
        ]

    async def get_connection_stats(self) -> ConnectionStats:
        """Obtém estatísticas atuais das conexões"""
        connections = list(self.connection_info.values())
        now = datetime.utcnow()
        idle_threshold = now - timedelta(minutes=self.idle_threshold_minutes)
        
        # Contar conexões por status
        active_count = len([c for c in connections if c.last_activity > idle_threshold])
        idle_count = len(connections) - active_count
        authenticated_count = len([c for c in connections if c.user_id])
        anonymous_count = len(connections) - authenticated_count
        
        # Calcular estatísticas
        total_channels = len(set(
            channel for conn in connections for channel in conn.channels
        ))
        
        total_messages = sum(conn.message_count for conn in connections)
        total_bytes = sum(conn.bytes_sent + conn.bytes_received for conn in connections)
        
        # Duração média de conexão
        if connections:
            durations = [(now - conn.connected_at).total_seconds() for conn in connections]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0.0
        
        # Pico de conexões (do histórico)
        peak_connections = len(connections)
        peak_time = now
        
        if self.stats_history:
            max_stat = max(self.stats_history, key=lambda x: x.total_connections)
            if max_stat.total_connections > peak_connections:
                peak_connections = max_stat.total_connections
                peak_time = max_stat.peak_connections_time
        
        return ConnectionStats(
            total_connections=len(connections),
            active_connections=active_count,
            idle_connections=idle_count,
            authenticated_connections=authenticated_count,
            anonymous_connections=anonymous_count,
            total_channels=total_channels,
            total_messages_sent=total_messages,
            total_bytes_transferred=total_bytes,
            average_connection_duration=avg_duration,
            peak_connections=peak_connections,
            peak_connections_time=peak_time
        )

    async def disconnect_connection(self, connection_id: str, reason: str = "Admin disconnect") -> bool:
        """Desconecta uma conexão específica"""
        try:
            success = await self.websocket_manager.disconnect_connection(connection_id, reason)
            
            if success and connection_id in self.connection_info:
                self.connection_info[connection_id].status = 'disconnected'
                
                # Log da ação administrativa
                logger.info(
                    f"Admin disconnected connection {connection_id}: {reason}",
                    extra={
                        "connection_id": connection_id,
                        "reason": reason,
                        "action": "admin_disconnect"
                    }
                )
            
            return success
        except Exception as e:
            logger.error(f"Error disconnecting connection {connection_id}: {e}")
            return False

    async def disconnect_user_connections(self, user_id: str, reason: str = "Admin disconnect") -> int:
        """Desconecta todas as conexões de um usuário"""
        user_connections = await self.get_connections_by_user(user_id)
        disconnected_count = 0
        
        for connection in user_connections:
            if await self.disconnect_connection(connection.connection_id, reason):
                disconnected_count += 1
        
        logger.info(
            f"Admin disconnected {disconnected_count} connections for user {user_id}",
            extra={
                "user_id": user_id,
                "disconnected_count": disconnected_count,
                "reason": reason,
                "action": "admin_disconnect_user"
            }
        )
        
        return disconnected_count

    async def broadcast_admin_message(
        self, 
        message: str, 
        target_type: str = "all",  # "all", "user", "channel"
        target_id: Optional[str] = None
    ) -> int:
        """Envia mensagem administrativa"""
        admin_message = {
            "type": "admin_message",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        
        sent_count = 0
        
        try:
            if target_type == "all":
                # Broadcast para todas as conexões
                for connection_id in self.connection_info.keys():
                    await self.websocket_manager.send_to_connection(connection_id, admin_message)
                    sent_count += 1
            
            elif target_type == "user" and target_id:
                # Enviar para usuário específico
                await self.websocket_manager.send_to_user(target_id, admin_message)
                user_connections = await self.get_connections_by_user(target_id)
                sent_count = len(user_connections)
            
            elif target_type == "channel" and target_id:
                # Broadcast para canal específico
                await self.websocket_manager.broadcast_to_channel(target_id, admin_message)
                # Contar conexões no canal
                sent_count = len([
                    conn for conn in self.connection_info.values()
                    if target_id in conn.channels
                ])
            
            logger.info(
                f"Admin message sent to {sent_count} connections",
                extra={
                    "message": message,
                    "target_type": target_type,
                    "target_id": target_id,
                    "sent_count": sent_count,
                    "action": "admin_broadcast"
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending admin message: {e}")
        
        return sent_count

    async def get_channel_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtém informações sobre canais ativos"""
        channel_info = {}
        
        for connection in self.connection_info.values():
            for channel in connection.channels:
                if channel not in channel_info:
                    channel_info[channel] = {
                        "name": channel,
                        "connection_count": 0,
                        "authenticated_users": set(),
                        "anonymous_connections": 0,
                        "created_at": connection.connected_at,
                        "last_activity": connection.last_activity
                    }
                
                channel_info[channel]["connection_count"] += 1
                
                if connection.user_id:
                    channel_info[channel]["authenticated_users"].add(connection.user_id)
                else:
                    channel_info[channel]["anonymous_connections"] += 1
                
                # Atualizar última atividade
                if connection.last_activity > channel_info[channel]["last_activity"]:
                    channel_info[channel]["last_activity"] = connection.last_activity
        
        # Converter sets para listas para serialização
        for channel_data in channel_info.values():
            channel_data["authenticated_users"] = list(channel_data["authenticated_users"])
            channel_data["authenticated_user_count"] = len(channel_data["authenticated_users"])
            channel_data["created_at"] = channel_data["created_at"].isoformat()
            channel_data["last_activity"] = channel_data["last_activity"].isoformat()
        
        return channel_info

    async def update_connection_info(
        self,
        connection_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        channels: Optional[List[str]] = None,
        message_count_delta: int = 0,
        bytes_sent_delta: int = 0,
        bytes_received_delta: int = 0
    ):
        """Atualiza informações de uma conexão"""
        now = datetime.utcnow()
        
        if connection_id not in self.connection_info:
            # Nova conexão
            self.connection_info[connection_id] = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                connected_at=now,
                last_activity=now,
                channels=channels or [],
                message_count=0,
                bytes_sent=0,
                bytes_received=0,
                status='active'
            )
        else:
            # Atualizar conexão existente
            conn = self.connection_info[connection_id]
            
            if user_id is not None:
                conn.user_id = user_id
            if channels is not None:
                conn.channels = channels
            
            conn.message_count += message_count_delta
            conn.bytes_sent += bytes_sent_delta
            conn.bytes_received += bytes_received_delta
            conn.last_activity = now
            
            # Atualizar status baseado na atividade
            idle_threshold = now - timedelta(minutes=self.idle_threshold_minutes)
            conn.status = 'active' if conn.last_activity > idle_threshold else 'idle'

    async def remove_connection(self, connection_id: str):
        """Remove uma conexão do tracking"""
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]

    async def collect_stats(self):
        """Coleta estatísticas para histórico"""
        stats = await self.get_connection_stats()
        self.stats_history.append(stats)
        
        # Limitar tamanho do histórico
        if len(self.stats_history) > self.max_history_entries:
            self.stats_history = self.stats_history[-self.max_history_entries:]

    async def get_stats_history(
        self, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Obtém histórico de estatísticas"""
        # Filtrar por período
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_stats = []
        for stat in self.stats_history:
            if stat.peak_connections_time and stat.peak_connections_time > cutoff_time:
                stat_dict = asdict(stat)
                if stat_dict['peak_connections_time']:
                    stat_dict['peak_connections_time'] = stat.peak_connections_time.isoformat()
                filtered_stats.append(stat_dict)
        
        return filtered_stats

    async def cleanup_stale_connections(self):
        """Remove conexões obsoletas"""
        now = datetime.utcnow()
        stale_threshold = now - timedelta(hours=1)  # Conexões sem atividade há 1 hora
        
        stale_connections = [
            conn_id for conn_id, conn in self.connection_info.items()
            if conn.last_activity < stale_threshold
        ]
        
        for conn_id in stale_connections:
            await self.remove_connection(conn_id)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")

    async def start_background_tasks(self):
        """Inicia tarefas em background"""
        # Coleta de estatísticas a cada minuto
        asyncio.create_task(self._stats_collector())
        
        # Limpeza de conexões obsoletas a cada 10 minutos
        asyncio.create_task(self._cleanup_task())

    async def _stats_collector(self):
        """Task para coleta periódica de estatísticas"""
        while True:
            try:
                await self.collect_stats()
                await asyncio.sleep(60)  # Coletar a cada minuto
            except Exception as e:
                logger.error(f"Error in stats collector: {e}")
                await asyncio.sleep(60)

    async def _cleanup_task(self):
        """Task para limpeza periódica"""
        while True:
            try:
                await self.cleanup_stale_connections()
                await asyncio.sleep(600)  # Limpar a cada 10 minutos
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(600)