"""
Testes para o WebSocketRepository.

Este módulo contém testes para o WebSocketRepository, responsável por
armazenar e recuperar informações sobre conexões WebSocket.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.repositories.websocket_repository import WebSocketRepository
from app.models.websocket_models import (
    WebSocketConnection,
    WebSocketConnectionStatus,
    WebSocketNotification
)


@pytest.fixture
def mock_redis():
    """
    Mock para o cliente Redis.
    
    Returns:
        MagicMock: Mock para o cliente Redis
    """
    redis_mock = MagicMock()
    redis_mock.hset = AsyncMock()
    redis_mock.hget = AsyncMock()
    redis_mock.hgetall = AsyncMock()
    redis_mock.exists = AsyncMock(return_value=True)
    redis_mock.expire = AsyncMock()
    redis_mock.sadd = AsyncMock()
    redis_mock.srem = AsyncMock()
    redis_mock.lpush = AsyncMock()
    redis_mock.ltrim = AsyncMock()
    redis_mock.keys = AsyncMock(return_value=[b"ws:active_users:user1", b"ws:active_users:user2"])
    redis_mock.scard = AsyncMock(return_value=5)
    redis_mock.smembers = AsyncMock(return_value=[b"conn1", b"conn2"])
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.zadd = AsyncMock()
    redis_mock.zrevrange = AsyncMock(return_value=[b"notif1", b"notif2"])
    redis_mock.delete = AsyncMock()
    redis_mock.zrem = AsyncMock()
    return redis_mock


@pytest.fixture
def websocket_repository(mock_redis):
    """
    Instância do WebSocketRepository para testes.
    
    Args:
        mock_redis: Mock para o cliente Redis
        
    Returns:
        WebSocketRepository: Instância do WebSocketRepository
    """
    return WebSocketRepository(mock_redis)


@pytest.mark.asyncio
async def test_save_connection(websocket_repository, mock_redis):
    """
    Testa o salvamento de uma conexão WebSocket.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    connection = WebSocketConnection(
        connection_id="conn123",
        user_id="user123",
        status=WebSocketConnectionStatus.CONNECTED,
        connected_at=datetime.now(),
        last_activity=datetime.now(),
        subscribed_channels=["channel1", "channel2"],
        client_info={"ip": "127.0.0.1", "user_agent": "test-agent"}
    )
    
    # Act
    result = await websocket_repository.save_connection(connection)
    
    # Assert
    assert result == "conn123"
    mock_redis.hset.assert_called_once()
    mock_redis.expire.assert_called_once()
    mock_redis.sadd.assert_called()
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()


@pytest.mark.asyncio
async def test_update_connection(websocket_repository, mock_redis):
    """
    Testa a atualização de uma conexão WebSocket.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    connection_id = "conn123"
    updates = {
        "status": WebSocketConnectionStatus.DISCONNECTED,
        "last_activity": datetime.now(),
        "subscribed_channels": ["channel1", "channel2"],
        "client_info": {"ip": "127.0.0.1", "user_agent": "test-agent"}
    }
    
    # Mock para hget
    mock_redis.hget.return_value = b"{}"
    
    # Act
    result = await websocket_repository.update_connection(connection_id, updates)
    
    # Assert
    assert result is True
    mock_redis.exists.assert_called_once()
    mock_redis.hset.assert_called_once()
    mock_redis.srem.assert_called_once()


@pytest.mark.asyncio
async def test_get_connection(websocket_repository, mock_redis):
    """
    Testa a obtenção de uma conexão WebSocket.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    connection_id = "conn123"
    mock_data = {
        b"user_id": b"user123",
        b"status": b"connected",
        b"connected_at": datetime.now().isoformat().encode(),
        b"last_activity": datetime.now().isoformat().encode(),
        b"subscribed_channels": b'["channel1", "channel2"]',
        b"client_info": b'{"ip": "127.0.0.1", "user_agent": "test-agent"}'
    }
    mock_redis.hgetall.return_value = mock_data
    
    # Act
    result = await websocket_repository.get_connection(connection_id)
    
    # Assert
    assert result is not None
    assert result.connection_id == connection_id
    assert result.user_id == "user123"
    assert result.status == WebSocketConnectionStatus.CONNECTED
    assert len(result.subscribed_channels) == 2
    assert result.client_info["ip"] == "127.0.0.1"
    mock_redis.exists.assert_called_once()
    mock_redis.hgetall.assert_called_once()


@pytest.mark.asyncio
async def test_delete_connection(websocket_repository, mock_redis):
    """
    Testa a exclusão de uma conexão WebSocket.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    connection_id = "conn123"
    mock_redis.hget.return_value = b"user123"
    
    # Act
    result = await websocket_repository.delete_connection(connection_id)
    
    # Assert
    assert result is True
    mock_redis.exists.assert_called_once()
    mock_redis.hget.assert_called_once()
    mock_redis.lpush.assert_called_once()
    mock_redis.srem.assert_called()
    mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_save_notification(websocket_repository, mock_redis):
    """
    Testa o salvamento de uma notificação.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    notification = WebSocketNotification(
        id="notif123",
        user_id="user123",
        type="info",
        title="Test Notification",
        message="This is a test notification",
        read=False,
        created_at=datetime.now(),
        action={"type": "open", "url": "/test"}
    )
    
    # Act
    result = await websocket_repository.save_notification(notification)
    
    # Assert
    assert result == "notif123"
    mock_redis.hset.assert_called_once()
    mock_redis.expire.assert_called_once()
    mock_redis.zadd.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_notifications(websocket_repository, mock_redis):
    """
    Testa a obtenção de notificações de um usuário.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    mock_data = {
        b"id": b"notif1",
        b"user_id": b"user123",
        b"type": b"info",
        b"title": b"Test Notification",
        b"message": b"This is a test notification",
        b"read": b"false",
        b"created_at": datetime.now().isoformat().encode(),
        b"action": b'{"type": "open", "url": "/test"}'
    }
    mock_redis.hgetall.return_value = mock_data
    
    # Act
    result = await websocket_repository.get_user_notifications(user_id)
    
    # Assert
    assert len(result) == 2
    assert result[0].id == "notif1"
    assert result[0].user_id == "user123"
    assert result[0].type == "info"
    assert result[0].title == "Test Notification"
    assert result[0].read is False
    assert result[0].action["type"] == "open"
    mock_redis.zrevrange.assert_called_once()
    mock_redis.hgetall.assert_called()


@pytest.mark.asyncio
async def test_mark_notification_as_read(websocket_repository, mock_redis):
    """
    Testa a marcação de uma notificação como lida.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    notification_id = "notif123"
    
    # Act
    result = await websocket_repository.mark_notification_as_read(user_id, notification_id)
    
    # Assert
    assert result is True
    mock_redis.exists.assert_called_once()
    mock_redis.hset.assert_called_once_with(
        f"{websocket_repository.notification_key_prefix}{user_id}:{notification_id}",
        "read",
        "true"
    )


@pytest.mark.asyncio
async def test_delete_notification(websocket_repository, mock_redis):
    """
    Testa a exclusão de uma notificação.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    notification_id = "notif123"
    
    # Act
    result = await websocket_repository.delete_notification(user_id, notification_id)
    
    # Assert
    assert result is True
    mock_redis.exists.assert_called_once()
    mock_redis.zrem.assert_called_once()
    mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats(websocket_repository, mock_redis):
    """
    Testa a obtenção de estatísticas de WebSocket.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    mock_redis.hgetall.return_value = {
        b"user_id": b"user123",
        b"status": b"connected",
        b"connected_at": datetime.now().isoformat().encode(),
        b"last_activity": datetime.now().isoformat().encode(),
        b"subscribed_channels": b'["channel1", "channel2"]',
        b"client_info": b'{"ip": "127.0.0.1", "user_agent": "test-agent"}'
    }
    
    # Act
    result = await websocket_repository.get_stats()
    
    # Assert
    assert result.total_connections == 5
    assert result.active_users == 2
    assert isinstance(result.channels, dict)
    assert result.connection_rate >= 0
    assert result.message_rate >= 0
    assert result.uptime >= 0
    mock_redis.scard.assert_called_once()
    mock_redis.keys.assert_called_once()
    mock_redis.smembers.assert_called_once()


@pytest.mark.asyncio
async def test_clean_idle_connections(websocket_repository, mock_redis):
    """
    Testa a limpeza de conexões ociosas.
    
    Args:
        websocket_repository: Instância do WebSocketRepository
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    idle_timeout = 30
    
    # Mock para get_connection
    old_time = datetime.now() - timedelta(minutes=idle_timeout + 10)
    connection = WebSocketConnection(
        connection_id="conn1",
        user_id="user123",
        status=WebSocketConnectionStatus.CONNECTED,
        connected_at=old_time,
        last_activity=old_time,
        subscribed_channels=[],
        client_info={}
    )
    
    with patch.object(websocket_repository, 'get_connection', return_value=connection):
        # Act
        result = await websocket_repository.clean_idle_connections(idle_timeout)
        
        # Assert
        assert result == 2  # Dois IDs de conexão no mock
        mock_redis.smembers.assert_called_once()
        mock_redis.srem.assert_called()