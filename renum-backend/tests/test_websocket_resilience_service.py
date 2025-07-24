"""
Testes para o WebSocketResilienceService.

Este módulo contém testes para o WebSocketResilienceService, responsável pela
resiliência das conexões WebSocket.
"""

import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.websocket_resilience_service import (
    WebSocketResilienceService,
    RateLimiter,
    MessageBuffer,
    CircuitBreaker
)


@pytest.fixture
def mock_redis():
    """
    Mock para o cliente Redis.
    
    Returns:
        MagicMock: Mock para o cliente Redis
    """
    redis_mock = MagicMock()
    redis_mock.lpush = AsyncMock()
    redis_mock.ltrim = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.llen = AsyncMock(return_value=0)
    redis_mock.delete = AsyncMock()
    redis_mock.keys = AsyncMock(return_value=[])
    return redis_mock


@pytest.fixture
def mock_repository():
    """
    Mock para o repositório WebSocket.
    
    Returns:
        MagicMock: Mock para o repositório WebSocket
    """
    repository_mock = MagicMock()
    repository_mock.log_message = AsyncMock()
    return repository_mock


@pytest.fixture
def resilience_service(mock_redis, mock_repository):
    """
    Instância do WebSocketResilienceService para testes.
    
    Args:
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
        
    Returns:
        WebSocketResilienceService: Instância do WebSocketResilienceService
    """
    return WebSocketResilienceService(mock_redis, mock_repository)


def test_rate_limiter():
    """Testa o limitador de taxa."""
    # Arrange
    rate_limiter = RateLimiter(3, 1.0)  # 3 requisições por segundo
    
    # Act & Assert
    assert rate_limiter.is_allowed("user1") is True  # 1ª requisição
    assert rate_limiter.is_allowed("user1") is True  # 2ª requisição
    assert rate_limiter.is_allowed("user1") is True  # 3ª requisição
    assert rate_limiter.is_allowed("user1") is False  # 4ª requisição (limite excedido)
    
    # Outro usuário não deve ser afetado
    assert rate_limiter.is_allowed("user2") is True
    
    # Verifica contadores
    assert rate_limiter.get_remaining("user1") == 0
    assert rate_limiter.get_remaining("user2") == 2
    
    # Verifica tempo de reset
    assert rate_limiter.get_reset_time("user1") > 0
    assert rate_limiter.get_reset_time("user1") <= 1.0


def test_message_buffer():
    """Testa o buffer de mensagens."""
    # Arrange
    buffer = MessageBuffer(3, 60)  # 3 mensagens, TTL de 60 segundos
    
    # Act & Assert
    assert buffer.add_message("user1", {"id": 1, "text": "Message 1"}) is True
    assert buffer.add_message("user1", {"id": 2, "text": "Message 2"}) is True
    assert buffer.add_message("user1", {"id": 3, "text": "Message 3"}) is True
    
    # Verifica que o buffer está cheio
    assert len(buffer.get_messages("user1")) == 3
    
    # Adiciona mais uma mensagem (deve remover a mais antiga)
    assert buffer.add_message("user1", {"id": 4, "text": "Message 4"}) is True
    messages = buffer.get_messages("user1")
    assert len(messages) == 3
    assert messages[0]["id"] == 2  # A mensagem 1 foi removida
    
    # Limpa o buffer
    buffer.clear_messages("user1")
    assert len(buffer.get_messages("user1")) == 0


def test_circuit_breaker():
    """Testa o circuit breaker."""
    # Arrange
    circuit_breaker = CircuitBreaker(3, 0.1, 0.2)  # 3 falhas, recovery 0.1s, reset 0.2s
    
    # Act & Assert
    assert circuit_breaker.is_allowed("user1") is True  # Inicialmente permitido
    
    # Registra falhas
    circuit_breaker.record_failure("user1")
    circuit_breaker.record_failure("user1")
    assert circuit_breaker.is_allowed("user1") is True  # Ainda permitido
    
    # Registra mais uma falha (limite atingido)
    circuit_breaker.record_failure("user1")
    assert circuit_breaker.is_allowed("user1") is False  # Agora bloqueado
    assert circuit_breaker.get_state("user1") == CircuitBreaker.State.OPEN
    
    # Espera o tempo de recovery
    time.sleep(0.15)
    assert circuit_breaker.is_allowed("user1") is True  # Permitido novamente (half-open)
    assert circuit_breaker.get_state("user1") == CircuitBreaker.State.HALF_OPEN
    
    # Registra sucesso
    circuit_breaker.record_success("user1")
    assert circuit_breaker.is_allowed("user1") is True  # Permitido
    assert circuit_breaker.get_state("user1") == CircuitBreaker.State.CLOSED
    
    # Reset manual
    circuit_breaker.record_failure("user1")
    circuit_breaker.reset("user1")
    assert circuit_breaker.get_state("user1") == CircuitBreaker.State.CLOSED


@pytest.mark.asyncio
async def test_check_rate_limit(resilience_service, mock_repository):
    """
    Testa a verificação de limites de taxa.
    
    Args:
        resilience_service: Instância do WebSocketResilienceService
        mock_repository: Mock para o repositório WebSocket
    """
    # Arrange
    user_id = "user123"
    ip = "127.0.0.1"
    
    # Act
    result = await resilience_service.check_rate_limit(user_id, ip)
    
    # Assert
    assert result["allowed"] is True
    assert "global" in result
    assert "user" in result
    assert "ip" in result
    assert "circuit" in result
    
    # Simula limite excedido
    resilience_service.user_rate_limiter.max_requests = 0
    
    # Act
    result = await resilience_service.check_rate_limit(user_id, ip)
    
    # Assert
    assert result["allowed"] is False
    mock_repository.log_message.assert_called_once()


@pytest.mark.asyncio
async def test_buffer_message(resilience_service, mock_redis):
    """
    Testa o armazenamento de mensagens no buffer.
    
    Args:
        resilience_service: Instância do WebSocketResilienceService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, world!"}
    
    # Act
    result = await resilience_service.buffer_message(user_id, message)
    
    # Assert
    assert result is True
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()
    mock_redis.expire.assert_called_once()
    
    # Verifica que a mensagem está no buffer em memória
    messages = resilience_service.message_buffer.get_messages(user_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello, world!"


@pytest.mark.asyncio
async def test_get_buffered_messages(resilience_service, mock_redis):
    """
    Testa a obtenção de mensagens do buffer.
    
    Args:
        resilience_service: Instância do WebSocketResilienceService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, world!"}
    
    # Adiciona a mensagem ao buffer em memória
    resilience_service.message_buffer.add_message(user_id, message)
    
    # Mock para lrange
    mock_redis.lrange.return_value = [json.dumps({"type": "test", "content": "Hello from Redis!"}).encode()]
    
    # Act
    messages = await resilience_service.get_buffered_messages(user_id)
    
    # Assert
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello, world!"
    assert messages[1]["content"] == "Hello from Redis!"
    mock_redis.lrange.assert_called_once()


@pytest.mark.asyncio
async def test_clear_buffered_messages(resilience_service, mock_redis):
    """
    Testa a limpeza de mensagens do buffer.
    
    Args:
        resilience_service: Instância do WebSocketResilienceService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, world!"}
    
    # Adiciona a mensagem ao buffer em memória
    resilience_service.message_buffer.add_message(user_id, message)
    
    # Act
    await resilience_service.clear_buffered_messages(user_id)
    
    # Assert
    assert len(resilience_service.message_buffer.get_messages(user_id)) == 0
    mock_redis.delete.assert_called_once()


def test_circuit_breaker_integration(resilience_service):
    """
    Testa a integração com o circuit breaker.
    
    Args:
        resilience_service: Instância do WebSocketResilienceService
    """
    # Arrange
    user_id = "user123"
    
    # Act & Assert
    assert resilience_service.is_circuit_allowed(user_id) is True
    
    # Registra falhas
    for _ in range(5):
        resilience_service.record_failure(user_id)
    
    # Verifica que o circuit breaker está aberto
    assert resilience_service.is_circuit_allowed(user_id) is False
    
    # Reset do circuit breaker
    resilience_service.reset_circuit(user_id)
    
    # Verifica que o circuit breaker está fechado novamente
    assert resilience_service.is_circuit_allowed(user_id) is True