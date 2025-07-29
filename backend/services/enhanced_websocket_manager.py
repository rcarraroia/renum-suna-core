"""
EnhancedWebSocketManager - Gerenciador avançado de WebSocket com pool de conexões

Este módulo implementa um sistema otimizado de gerenciamento de conexões WebSocket
com pool de conexões, verificação de recursos e sistema de retry robusto.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import weakref
from collections import defaultdict, deque
import threading
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect
from services.improved_token_validator import ImprovedTokenValidator
from services.websocket_auth_fallback import WebSocketAuthFallback

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Estados possíveis de uma conexão WebSocket."""
    PENDING = "pending"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ResourceStatus(Enum):
    """Status dos recursos do sistema."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


@dataclass
class ConnectionInfo:
    """Informações de uma conexão WebSocket."""
    connection_id: str
    user_id: str
    websocket: WebSocket
    state: ConnectionState
    created_at: datetime
    last_activity: datetime
    auth_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0


@dataclass
class PoolConfiguration:
    """Configuração do pool de conexões."""
    max_connections: int = 500
    max_connections_per_user: int = 10
    handshake_timeout: int = 30
    heartbeat_interval: int = 30
    idle_timeout: int = 300  # 5 minutos
    retry_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_exponential_base: float = 2.0
    
    # Limites de recursos
    max_memory_percent: float = 85.0
    max_cpu_percent: float = 90.0
    max_connections_per_ip: int = 50
    
    # Configurações de limpeza
    cleanup_interval: int = 60  # segundos
    stats_retention_hours: int = 24


@dataclass
class ResourceMetrics:
    """Métricas de recursos do sistema."""
    timestamp: datetime
    memory_percent: float
    cpu_percent: float
    active_connections: int
    pending_connections: int
    total_connections: int
    connections_per_second: float
    bytes_per_second: float
    errors_per_minute: int


class ConnectionPool:
    """Pool de conexões WebSocket otimizado."""
    
    def __init__(self, config: PoolConfiguration):
        self.config = config
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.ip_connections: Dict[str, Set[str]] = defaultdict(set)
        self.pending_connections: Set[str] = set()
        
        # Métricas e estatísticas
        self.metrics_history: deque = deque(maxlen=1000)
        self.connection_stats = {
            'total_created': 0,
            'total_closed': 0,
            'total_errors': 0,
            'peak_connections': 0,
            'avg_connection_duration': 0.0
        }
        
        # Controle de recursos
        self._resource_check_lock = asyncio.Lock()
        self._last_resource_check = 0
        self._resource_cache_ttl = 5  # segundos
        self._cached_resource_status = ResourceStatus.HEALTHY
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"ConnectionPool initialized with max_connections={config.max_connections}")
    
    async def start(self):
        """Inicia o pool de conexões."""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("ConnectionPool started")
    
    async def stop(self):
        """Para o pool de conexões."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Fechar todas as conexões
        await self._close_all_connections()
        logger.info("ConnectionPool stopped")
    
    async def can_accept_connection(self, user_id: str, client_ip: str) -> Tuple[bool, str]:
        """
        Verifica se pode aceitar uma nova conexão.
        
        Returns:
            Tuple[bool, str]: (pode_aceitar, motivo_se_nao)
        """
        # Verificar limite total
        if len(self.connections) >= self.config.max_connections:
            return False, f"Limite máximo de conexões atingido ({self.config.max_connections})"
        
        # Verificar limite por usuário
        user_conn_count = len(self.user_connections.get(user_id, set()))
        if user_conn_count >= self.config.max_connections_per_user:
            return False, f"Limite de conexões por usuário atingido ({self.config.max_connections_per_user})"
        
        # Verificar limite por IP
        ip_conn_count = len(self.ip_connections.get(client_ip, set()))
        if ip_conn_count >= self.config.max_connections_per_ip:
            return False, f"Limite de conexões por IP atingido ({self.config.max_connections_per_ip})"
        
        # Verificar recursos do sistema (apenas bloquear se realmente crítico)
        resource_status = await self._check_system_resources()
        if resource_status == ResourceStatus.OVERLOADED:
            # Permitir algumas conexões mesmo com recursos altos, mas com limite reduzido
            if len(self.connections) >= self.config.max_connections * 0.8:
                return False, "Sistema sobrecarregado - recursos insuficientes"
        
        return True, "OK"
    
    async def add_connection(self, connection_id: str, user_id: str, websocket: WebSocket,
                           client_ip: str, auth_method: str = "jwt") -> bool:
        """
        Adiciona uma conexão ao pool.
        
        Returns:
            bool: True se adicionada com sucesso
        """
        try:
            # Verificar se pode aceitar
            can_accept, reason = await self.can_accept_connection(user_id, client_ip)
            if not can_accept:
                logger.warning(f"Conexão rejeitada: {reason}")
                return False
            
            # Criar info da conexão
            now = datetime.now()
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                state=ConnectionState.CONNECTED,
                created_at=now,
                last_activity=now,
                auth_method=auth_method,
                metadata={"client_ip": client_ip}
            )
            
            # Adicionar ao pool
            self.connections[connection_id] = connection_info
            self.user_connections[user_id].add(connection_id)
            self.ip_connections[client_ip].add(connection_id)
            
            # Remover de pendentes se estava lá
            self.pending_connections.discard(connection_id)
            
            # Atualizar estatísticas
            self.connection_stats['total_created'] += 1
            current_count = len(self.connections)
            if current_count > self.connection_stats['peak_connections']:
                self.connection_stats['peak_connections'] = current_count
            
            logger.info(f"Conexão adicionada ao pool: {connection_id} (usuário: {user_id}, total: {current_count})")
            return True
            
        except Exception as e:
            logger.error(f"Erro adicionando conexão ao pool: {str(e)}")
            return False
    
    async def remove_connection(self, connection_id: str) -> bool:
        """
        Remove uma conexão do pool.
        
        Returns:
            bool: True se removida com sucesso
        """
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return False
            
            # Calcular duração da conexão
            duration = (datetime.now() - connection_info.created_at).total_seconds()
            
            # Remover das estruturas de dados
            del self.connections[connection_id]
            
            user_id = connection_info.user_id
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            
            client_ip = connection_info.metadata.get("client_ip")
            if client_ip:
                self.ip_connections[client_ip].discard(connection_id)
                if not self.ip_connections[client_ip]:
                    del self.ip_connections[client_ip]
            
            self.pending_connections.discard(connection_id)
            
            # Atualizar estatísticas
            self.connection_stats['total_closed'] += 1
            
            # Atualizar duração média
            total_connections = self.connection_stats['total_closed']
            current_avg = self.connection_stats['avg_connection_duration']
            self.connection_stats['avg_connection_duration'] = (
                (current_avg * (total_connections - 1) + duration) / total_connections
            )
            
            logger.info(f"Conexão removida do pool: {connection_id} (duração: {duration:.1f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Erro removendo conexão do pool: {str(e)}")
            return False
    
    async def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Obtém informações de uma conexão."""
        return self.connections.get(connection_id)
    
    async def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Obtém todas as conexões de um usuário."""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[conn_id] for conn_id in connection_ids if conn_id in self.connections]
    
    async def update_activity(self, connection_id: str, bytes_delta: int = 0, 
                            message_delta: int = 0, sent: bool = True):
        """Atualiza atividade de uma conexão."""
        connection_info = self.connections.get(connection_id)
        if connection_info:
            connection_info.last_activity = datetime.now()
            
            if sent:
                connection_info.bytes_sent += bytes_delta
                connection_info.messages_sent += message_delta
            else:
                connection_info.bytes_received += bytes_delta
                connection_info.messages_received += message_delta
    
    async def _check_system_resources(self) -> ResourceStatus:
        """Verifica recursos do sistema com cache."""
        now = time.time()
        
        async with self._resource_check_lock:
            # Usar cache se ainda válido
            if now - self._last_resource_check < self._resource_cache_ttl:
                return self._cached_resource_status
            
            try:
                # Verificar memória
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Verificar CPU
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Determinar status
                if (memory_percent >= self.config.max_memory_percent or 
                    cpu_percent >= self.config.max_cpu_percent):
                    status = ResourceStatus.OVERLOADED
                elif (memory_percent >= self.config.max_memory_percent * 0.9 or 
                      cpu_percent >= self.config.max_cpu_percent * 0.9):
                    status = ResourceStatus.CRITICAL
                elif (memory_percent >= self.config.max_memory_percent * 0.8 or 
                      cpu_percent >= self.config.max_cpu_percent * 0.8):
                    status = ResourceStatus.WARNING
                else:
                    status = ResourceStatus.HEALTHY
                
                # Atualizar cache
                self._last_resource_check = now
                self._cached_resource_status = status
                
                # Adicionar métricas
                metrics = ResourceMetrics(
                    timestamp=datetime.now(),
                    memory_percent=memory_percent,
                    cpu_percent=cpu_percent,
                    active_connections=len(self.connections),
                    pending_connections=len(self.pending_connections),
                    total_connections=len(self.connections) + len(self.pending_connections),
                    connections_per_second=0.0,  # Calculado em outro lugar
                    bytes_per_second=0.0,  # Calculado em outro lugar
                    errors_per_minute=0  # Calculado em outro lugar
                )
                self.metrics_history.append(metrics)
                
                return status
                
            except Exception as e:
                logger.error(f"Erro verificando recursos do sistema: {str(e)}")
                return ResourceStatus.WARNING
    
    async def _cleanup_loop(self):
        """Loop de limpeza periódica."""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_idle_connections()
                await self._cleanup_old_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de limpeza: {str(e)}")
    
    async def _cleanup_idle_connections(self):
        """Remove conexões inativas."""
        now = datetime.now()
        idle_threshold = timedelta(seconds=self.config.idle_timeout)
        
        idle_connections = []
        for connection_id, connection_info in self.connections.items():
            if now - connection_info.last_activity > idle_threshold:
                idle_connections.append(connection_id)
        
        for connection_id in idle_connections:
            logger.info(f"Removendo conexão inativa: {connection_id}")
            connection_info = self.connections.get(connection_id)
            if connection_info:
                try:
                    await connection_info.websocket.close(code=1000, reason="Idle timeout")
                except:
                    pass  # Ignorar erros ao fechar
                await self.remove_connection(connection_id)
    
    async def _cleanup_old_metrics(self):
        """Remove métricas antigas."""
        if not self.metrics_history:
            return
            
        cutoff_time = datetime.now() - timedelta(hours=self.config.stats_retention_hours)
        
        # Remover métricas antigas
        while (self.metrics_history and 
               self.metrics_history[0].timestamp < cutoff_time):
            self.metrics_history.popleft()
    
    async def _close_all_connections(self):
        """Fecha todas as conexões."""
        connection_ids = list(self.connections.keys())
        
        for connection_id in connection_ids:
            connection_info = self.connections.get(connection_id)
            if connection_info:
                try:
                    await connection_info.websocket.close(code=1001, reason="Server shutdown")
                except:
                    pass  # Ignorar erros ao fechar
                await self.remove_connection(connection_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do pool."""
        current_metrics = None
        if self.metrics_history:
            current_metrics = self.metrics_history[-1]
        
        return {
            "pool_config": {
                "max_connections": self.config.max_connections,
                "max_connections_per_user": self.config.max_connections_per_user,
                "handshake_timeout": self.config.handshake_timeout,
                "heartbeat_interval": self.config.heartbeat_interval
            },
            "current_state": {
                "active_connections": len(self.connections),
                "pending_connections": len(self.pending_connections),
                "unique_users": len(self.user_connections),
                "unique_ips": len(self.ip_connections),
                "resource_status": self._cached_resource_status.value if hasattr(self, '_cached_resource_status') else "unknown"
            },
            "lifetime_stats": self.connection_stats,
            "current_metrics": {
                "memory_percent": current_metrics.memory_percent if current_metrics else 0,
                "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                "timestamp": current_metrics.timestamp.isoformat() if current_metrics else None
            } if current_metrics else None,
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "connections_by_ip": {
                ip: len(connections) 
                for ip, connections in self.ip_connections.items()
            }
        }


class EnhancedWebSocketManager:
    """Gerenciador avançado de WebSocket com pool de conexões."""
    
    def __init__(self, config: Optional[PoolConfiguration] = None):
        self.config = config or PoolConfiguration()
        self.pool = ConnectionPool(self.config)
        self.token_validator = ImprovedTokenValidator()
        self.auth_fallback = WebSocketAuthFallback()
        
        # Sistema de retry com backoff exponencial
        self.retry_delays: Dict[str, float] = {}
        
        logger.info("EnhancedWebSocketManager initialized")
    
    async def start(self):
        """Inicia o gerenciador."""
        await self.pool.start()
        logger.info("EnhancedWebSocketManager started")
    
    async def stop(self):
        """Para o gerenciador."""
        await self.pool.stop()
        logger.info("EnhancedWebSocketManager stopped")
    
    @asynccontextmanager
    async def connection_context(self, websocket: WebSocket, token: Optional[str] = None,
                               client_ip: str = "unknown"):
        """Context manager para gerenciar conexões WebSocket."""
        connection_id = f"conn_{int(time.time() * 1000)}_{id(websocket)}"
        
        try:
            # Verificar recursos antes de aceitar
            can_accept, reason = await self.pool.can_accept_connection("unknown", client_ip)
            if not can_accept:
                await websocket.close(code=1013, reason=reason)
                raise Exception(f"Conexão rejeitada: {reason}")
            
            # Aceitar conexão WebSocket
            await websocket.accept()
            
            # Autenticar com retry
            auth_result = await self._authenticate_with_retry(websocket, token, connection_id)
            
            if not auth_result["success"]:
                await websocket.close(code=1008, reason=auth_result["error"])
                raise Exception(f"Autenticação falhou: {auth_result['error']}")
            
            user_id = auth_result["user_id"]
            auth_method = auth_result.get("auth_method", "jwt")
            
            # Adicionar ao pool
            success = await self.pool.add_connection(
                connection_id, user_id, websocket, client_ip, auth_method
            )
            
            if not success:
                await websocket.close(code=1013, reason="Falha ao adicionar ao pool")
                raise Exception("Falha ao adicionar conexão ao pool")
            
            # Enviar confirmação
            await self._send_message(websocket, {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Conexão estabelecida: {connection_id} (usuário: {user_id})")
            
            yield connection_id, user_id
            
        except Exception as e:
            logger.error(f"Erro no contexto de conexão: {str(e)}")
            raise
        finally:
            # Limpar conexão
            await self.pool.remove_connection(connection_id)
            self.retry_delays.pop(connection_id, None)
    
    async def _authenticate_with_retry(self, websocket: WebSocket, token: Optional[str],
                                     connection_id: str) -> dict:
        """Autentica com sistema de retry e backoff exponencial."""
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Calcular delay para retry
                if attempt > 0:
                    delay = min(
                        self.config.retry_base_delay * (self.config.retry_exponential_base ** (attempt - 1)),
                        self.config.retry_max_delay
                    )
                    logger.info(f"Retry {attempt} para {connection_id} após {delay:.1f}s")
                    await asyncio.sleep(delay)
                
                # Tentar autenticação
                if token and token.strip():
                    validation_result = await self.token_validator.validate_token_async(token)
                    if validation_result.valid:
                        return {
                            "success": True,
                            "user_id": validation_result.user_id,
                            "auth_method": "jwt"
                        }
                
                # Tentar fallback
                fallback_result = await self.auth_fallback.authenticate_fallback(websocket, connection_id)
                if fallback_result["success"]:
                    return fallback_result
                
                # Se não é a última tentativa, continuar
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(f"Tentativa {attempt + 1} falhou para {connection_id}, tentando novamente...")
                    continue
                
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1} de autenticação: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    break
        
        return {
            "success": False,
            "error": f"Autenticação falhou após {self.config.retry_attempts} tentativas",
            "auth_method": "failed"
        }
    
    async def _send_message(self, websocket: WebSocket, message: dict):
        """Envia mensagem via WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Erro enviando mensagem: {str(e)}")
            raise
    
    async def send_to_user(self, user_id: str, message: dict) -> int:
        """Envia mensagem para todas as conexões de um usuário."""
        connections = await self.pool.get_user_connections(user_id)
        success_count = 0
        
        for connection_info in connections:
            try:
                await self._send_message(connection_info.websocket, message)
                await self.pool.update_activity(
                    connection_info.connection_id, 
                    bytes_delta=len(json.dumps(message).encode()),
                    message_delta=1,
                    sent=True
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Erro enviando para {connection_info.connection_id}: {str(e)}")
                # Remover conexão com falha
                await self.pool.remove_connection(connection_info.connection_id)
        
        return success_count
    
    async def broadcast(self, message: dict, exclude_user: Optional[str] = None) -> int:
        """Envia mensagem para todas as conexões ativas."""
        success_count = 0
        
        # Obter todas as conexões
        all_connections = list(self.pool.connections.values())
        
        for connection_info in all_connections:
            if exclude_user and connection_info.user_id == exclude_user:
                continue
                
            try:
                await self._send_message(connection_info.websocket, message)
                await self.pool.update_activity(
                    connection_info.connection_id,
                    bytes_delta=len(json.dumps(message).encode()),
                    message_delta=1,
                    sent=True
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Erro no broadcast para {connection_info.connection_id}: {str(e)}")
                # Remover conexão com falha
                await self.pool.remove_connection(connection_info.connection_id)
        
        return success_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do gerenciador."""
        pool_stats = self.pool.get_stats()
        
        return {
            "manager_info": {
                "class": "EnhancedWebSocketManager",
                "version": "1.0",
                "features": [
                    "connection_pool",
                    "resource_monitoring", 
                    "retry_with_backoff",
                    "idle_cleanup",
                    "per_user_limits",
                    "per_ip_limits"
                ]
            },
            "pool_stats": pool_stats,
            "retry_config": {
                "max_attempts": self.config.retry_attempts,
                "base_delay": self.config.retry_base_delay,
                "max_delay": self.config.retry_max_delay,
                "exponential_base": self.config.retry_exponential_base
            },
            "active_retries": len(self.retry_delays)
        }