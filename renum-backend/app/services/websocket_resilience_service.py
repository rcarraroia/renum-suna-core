"""
Serviço para resiliência de WebSocket.

Este módulo implementa o serviço para resiliência de WebSocket, incluindo
armazenamento temporário de mensagens não entregues, detecção de conexões zumbi
e limitação de taxa.
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Set, Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from uuid import UUID, uuid4

from app.core.logger import logger
from app.models.websocket_models import WebSocketMessage, WebSocketMessageType
from app.repositories.websocket_repository import WebSocketRepository


class RateLimiter:
    """Limitador de taxa para WebSocket."""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Inicializa o limitador de taxa.
        
        Args:
            max_requests: Número máximo de requisições permitidas
            time_window: Janela de tempo em segundos
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """
        Verifica se uma requisição é permitida.
        
        Args:
            key: Chave para identificar o cliente
            
        Returns:
            True se a requisição é permitida, False caso contrário
        """
        now = time.time()
        
        # Inicializa a lista de requisições se necessário
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove requisições antigas
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time <= self.time_window]
        
        # Verifica se o limite foi atingido
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Adiciona a requisição atual
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """
        Obtém o número de requisições restantes.
        
        Args:
            key: Chave para identificar o cliente
            
        Returns:
            Número de requisições restantes
        """
        now = time.time()
        
        # Inicializa a lista de requisições se necessário
        if key not in self.requests:
            return self.max_requests
        
        # Remove requisições antigas
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time <= self.time_window]
        
        # Retorna o número de requisições restantes
        return max(0, self.max_requests - len(self.requests[key]))
    
    def get_reset_time(self, key: str) -> float:
        """
        Obtém o tempo restante para resetar o limite.
        
        Args:
            key: Chave para identificar o cliente
            
        Returns:
            Tempo restante em segundos
        """
        now = time.time()
        
        # Inicializa a lista de requisições se necessário
        if key not in self.requests or not self.requests[key]:
            return 0.0
        
        # Obtém o tempo da requisição mais antiga
        oldest_request = min(self.requests[key])
        
        # Retorna o tempo restante
        return max(0.0, oldest_request + self.time_window - now)


class MessageBuffer:
    """Buffer de mensagens para WebSocket."""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Inicializa o buffer de mensagens.
        
        Args:
            max_size: Tamanho máximo do buffer
            ttl: Tempo de vida das mensagens em segundos
        """
        self.max_size = max_size
        self.ttl = ttl
        self.buffers: Dict[str, List[Dict[str, Any]]] = {}
        self.timestamps: Dict[str, List[float]] = {}
    
    def add_message(self, key: str, message: Dict[str, Any]) -> bool:
        """
        Adiciona uma mensagem ao buffer.
        
        Args:
            key: Chave para identificar o destinatário
            message: Mensagem a ser armazenada
            
        Returns:
            True se a mensagem foi adicionada, False caso contrário
        """
        now = time.time()
        
        # Inicializa o buffer se necessário
        if key not in self.buffers:
            self.buffers[key] = []
            self.timestamps[key] = []
        
        # Remove mensagens antigas
        self._clean_buffer(key)
        
        # Verifica se o buffer está cheio
        if len(self.buffers[key]) >= self.max_size:
            # Remove a mensagem mais antiga
            self.buffers[key].pop(0)
            self.timestamps[key].pop(0)
        
        # Adiciona a mensagem
        self.buffers[key].append(message)
        self.timestamps[key].append(now)
        
        return True
    
    def get_messages(self, key: str) -> List[Dict[str, Any]]:
        """
        Obtém as mensagens do buffer.
        
        Args:
            key: Chave para identificar o destinatário
            
        Returns:
            Lista de mensagens
        """
        # Inicializa o buffer se necessário
        if key not in self.buffers:
            return []
        
        # Remove mensagens antigas
        self._clean_buffer(key)
        
        # Retorna as mensagens
        return self.buffers[key].copy()
    
    def clear_messages(self, key: str) -> None:
        """
        Limpa as mensagens do buffer.
        
        Args:
            key: Chave para identificar o destinatário
        """
        if key in self.buffers:
            self.buffers[key] = []
            self.timestamps[key] = []
    
    def _clean_buffer(self, key: str) -> None:
        """
        Remove mensagens antigas do buffer.
        
        Args:
            key: Chave para identificar o destinatário
        """
        now = time.time()
        
        # Remove mensagens antigas
        if key in self.buffers and key in self.timestamps:
            valid_indices = [i for i, ts in enumerate(self.timestamps[key]) if now - ts <= self.ttl]
            self.buffers[key] = [self.buffers[key][i] for i in valid_indices]
            self.timestamps[key] = [self.timestamps[key][i] for i in valid_indices]


class CircuitBreaker:
    """Circuit breaker para WebSocket."""
    
    class State:
        """Estados do circuit breaker."""
        
        CLOSED = "closed"  # Funcionando normalmente
        OPEN = "open"  # Falhas detectadas, circuito aberto
        HALF_OPEN = "half_open"  # Tentando recuperar
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        reset_timeout: float = 60.0
    ):
        """
        Inicializa o circuit breaker.
        
        Args:
            failure_threshold: Número de falhas para abrir o circuito
            recovery_timeout: Tempo para tentar recuperar em segundos
            reset_timeout: Tempo para resetar o contador de falhas em segundos
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.reset_timeout = reset_timeout
        self.circuits: Dict[str, Dict[str, Any]] = {}
    
    def record_success(self, key: str) -> None:
        """
        Registra um sucesso.
        
        Args:
            key: Chave para identificar o circuito
        """
        now = time.time()
        
        # Inicializa o circuito se necessário
        if key not in self.circuits:
            self.circuits[key] = {
                "state": self.State.CLOSED,
                "failures": 0,
                "last_failure": 0,
                "last_attempt": now
            }
            return
        
        circuit = self.circuits[key]
        
        # Atualiza o estado do circuito
        if circuit["state"] == self.State.HALF_OPEN:
            circuit["state"] = self.State.CLOSED
            circuit["failures"] = 0
        elif circuit["state"] == self.State.CLOSED:
            # Reseta o contador de falhas se passou tempo suficiente
            if now - circuit["last_failure"] > self.reset_timeout:
                circuit["failures"] = 0
        
        circuit["last_attempt"] = now
    
    def record_failure(self, key: str) -> None:
        """
        Registra uma falha.
        
        Args:
            key: Chave para identificar o circuito
        """
        now = time.time()
        
        # Inicializa o circuito se necessário
        if key not in self.circuits:
            self.circuits[key] = {
                "state": self.State.CLOSED,
                "failures": 1,
                "last_failure": now,
                "last_attempt": now
            }
            return
        
        circuit = self.circuits[key]
        
        # Atualiza o estado do circuito
        if circuit["state"] == self.State.CLOSED:
            circuit["failures"] += 1
            if circuit["failures"] >= self.failure_threshold:
                circuit["state"] = self.State.OPEN
        elif circuit["state"] == self.State.HALF_OPEN:
            circuit["state"] = self.State.OPEN
        
        circuit["last_failure"] = now
        circuit["last_attempt"] = now
    
    def is_allowed(self, key: str) -> bool:
        """
        Verifica se uma operação é permitida.
        
        Args:
            key: Chave para identificar o circuito
            
        Returns:
            True se a operação é permitida, False caso contrário
        """
        now = time.time()
        
        # Inicializa o circuito se necessário
        if key not in self.circuits:
            self.circuits[key] = {
                "state": self.State.CLOSED,
                "failures": 0,
                "last_failure": 0,
                "last_attempt": now
            }
            return True
        
        circuit = self.circuits[key]
        
        # Verifica o estado do circuito
        if circuit["state"] == self.State.CLOSED:
            return True
        elif circuit["state"] == self.State.OPEN:
            # Verifica se passou tempo suficiente para tentar recuperar
            if now - circuit["last_failure"] > self.recovery_timeout:
                circuit["state"] = self.State.HALF_OPEN
                return True
            return False
        elif circuit["state"] == self.State.HALF_OPEN:
            return True
        
        return True
    
    def get_state(self, key: str) -> str:
        """
        Obtém o estado do circuito.
        
        Args:
            key: Chave para identificar o circuito
            
        Returns:
            Estado do circuito
        """
        if key not in self.circuits:
            return self.State.CLOSED
        
        return self.circuits[key]["state"]
    
    def reset(self, key: str) -> None:
        """
        Reseta o circuito.
        
        Args:
            key: Chave para identificar o circuito
        """
        if key in self.circuits:
            self.circuits[key] = {
                "state": self.State.CLOSED,
                "failures": 0,
                "last_failure": 0,
                "last_attempt": time.time()
            }


class WebSocketResilienceService:
    """Serviço para resiliência de WebSocket."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, repository: Optional[WebSocketRepository] = None):
        """
        Inicializa o serviço.
        
        Args:
            redis_client: Cliente Redis para armazenamento (opcional)
            repository: Repositório WebSocket (opcional)
        """
        self.redis = redis_client
        self.repository = repository
        
        # Limitadores de taxa
        self.global_rate_limiter = RateLimiter(1000, 60.0)  # 1000 requisições por minuto
        self.user_rate_limiter = RateLimiter(100, 60.0)  # 100 requisições por minuto por usuário
        self.ip_rate_limiter = RateLimiter(200, 60.0)  # 200 requisições por minuto por IP
        
        # Buffer de mensagens
        self.message_buffer = MessageBuffer(100, 3600)  # 100 mensagens por usuário, TTL de 1 hora
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(5, 30.0, 60.0)
        
        # Prefixos de chaves Redis
        self.rate_limit_prefix = "ws:rate_limit:"
        self.message_buffer_prefix = "ws:message_buffer:"
        self.circuit_breaker_prefix = "ws:circuit_breaker:"
        
        # Tarefa de limpeza
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 300  # segundos
        
        logger.info("WebSocket Resilience Service initialized")
    
    async def check_rate_limit(self, user_id: str, ip: str) -> Dict[str, Any]:
        """
        Verifica os limites de taxa.
        
        Args:
            user_id: ID do usuário
            ip: Endereço IP
            
        Returns:
            Dicionário com informações sobre os limites de taxa
        """
        # Verifica o limite global
        global_allowed = self.global_rate_limiter.is_allowed("global")
        
        # Verifica o limite por usuário
        user_allowed = self.user_rate_limiter.is_allowed(user_id)
        
        # Verifica o limite por IP
        ip_allowed = self.ip_rate_limiter.is_allowed(ip)
        
        # Verifica o circuit breaker
        circuit_allowed = self.circuit_breaker.is_allowed(user_id)
        
        # Calcula o resultado final
        allowed = global_allowed and user_allowed and ip_allowed and circuit_allowed
        
        # Obtém informações adicionais
        result = {
            "allowed": allowed,
            "global": {
                "allowed": global_allowed,
                "remaining": self.global_rate_limiter.get_remaining("global"),
                "reset": self.global_rate_limiter.get_reset_time("global")
            },
            "user": {
                "allowed": user_allowed,
                "remaining": self.user_rate_limiter.get_remaining(user_id),
                "reset": self.user_rate_limiter.get_reset_time(user_id)
            },
            "ip": {
                "allowed": ip_allowed,
                "remaining": self.ip_rate_limiter.get_remaining(ip),
                "reset": self.ip_rate_limiter.get_reset_time(ip)
            },
            "circuit": {
                "allowed": circuit_allowed,
                "state": self.circuit_breaker.get_state(user_id)
            }
        }
        
        # Registra no repositório
        if self.repository and not allowed:
            await self.repository.log_message({
                "event": "rate_limit",
                "user_id": user_id,
                "ip": ip,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
        
        return result
    
    async def buffer_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """
        Armazena uma mensagem no buffer.
        
        Args:
            user_id: ID do usuário
            message: Mensagem a ser armazenada
            
        Returns:
            True se a mensagem foi armazenada, False caso contrário
        """
        # Armazena a mensagem no buffer em memória
        result = self.message_buffer.add_message(user_id, message)
        
        # Armazena a mensagem no Redis
        if self.redis and result:
            buffer_key = f"{self.message_buffer_prefix}{user_id}"
            
            # Adiciona timestamp à mensagem
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            
            # Converte a mensagem para JSON
            json_message = json.dumps(message)
            
            # Adiciona a mensagem à lista
            await self.redis.lpush(buffer_key, json_message)
            
            # Limita o tamanho da lista
            await self.redis.ltrim(buffer_key, 0, self.message_buffer.max_size - 1)
            
            # Define TTL
            await self.redis.expire(buffer_key, self.message_buffer.ttl)
        
        return result
    
    async def get_buffered_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtém as mensagens armazenadas no buffer.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de mensagens
        """
        # Obtém as mensagens do buffer em memória
        messages = self.message_buffer.get_messages(user_id)
        
        # Obtém as mensagens do Redis
        if self.redis:
            buffer_key = f"{self.message_buffer_prefix}{user_id}"
            
            # Obtém as mensagens
            redis_messages = await self.redis.lrange(buffer_key, 0, -1)
            
            # Converte as mensagens de JSON
            for msg in redis_messages:
                try:
                    message = json.loads(msg)
                    
                    # Verifica se a mensagem já está no buffer em memória
                    if message not in messages:
                        messages.append(message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in Redis message buffer: {msg}")
        
        return messages
    
    async def clear_buffered_messages(self, user_id: str) -> None:
        """
        Limpa as mensagens armazenadas no buffer.
        
        Args:
            user_id: ID do usuário
        """
        # Limpa o buffer em memória
        self.message_buffer.clear_messages(user_id)
        
        # Limpa o buffer no Redis
        if self.redis:
            buffer_key = f"{self.message_buffer_prefix}{user_id}"
            await self.redis.delete(buffer_key)
    
    def record_success(self, user_id: str) -> None:
        """
        Registra um sucesso.
        
        Args:
            user_id: ID do usuário
        """
        self.circuit_breaker.record_success(user_id)
    
    def record_failure(self, user_id: str) -> None:
        """
        Registra uma falha.
        
        Args:
            user_id: ID do usuário
        """
        self.circuit_breaker.record_failure(user_id)
    
    def is_circuit_allowed(self, user_id: str) -> bool:
        """
        Verifica se o circuit breaker permite operações.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se operações são permitidas, False caso contrário
        """
        return self.circuit_breaker.is_allowed(user_id)
    
    def reset_circuit(self, user_id: str) -> None:
        """
        Reseta o circuit breaker.
        
        Args:
            user_id: ID do usuário
        """
        self.circuit_breaker.reset(user_id)
    
    async def start_cleanup_task(self) -> None:
        """Inicia a tarefa de limpeza."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self) -> None:
        """Para a tarefa de limpeza."""
        if self.cleanup_task is not None:
            self.cleanup_task.cancel()
            self.cleanup_task = None
    
    async def _cleanup_loop(self) -> None:
        """
        Limpa periodicamente recursos não utilizados.
        """
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                
                try:
                    # Limpa buffers de mensagens no Redis
                    if self.redis:
                        # Obtém todas as chaves de buffer
                        buffer_keys = await self.redis.keys(f"{self.message_buffer_prefix}*")
                        
                        # Verifica cada buffer
                        for key in buffer_keys:
                            # Verifica se o buffer está vazio
                            length = await self.redis.llen(key)
                            if length == 0:
                                await self.redis.delete(key)
                    
                    logger.debug("WebSocket resilience cleanup completed")
                    
                except Exception as e:
                    logger.error(f"Error in WebSocket resilience cleanup: {str(e)}")
                    
        except asyncio.CancelledError:
            logger.info("WebSocket resilience cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in WebSocket resilience cleanup loop: {str(e)}")


# Instância global do serviço de resiliência WebSocket
websocket_resilience_service = WebSocketResilienceService()