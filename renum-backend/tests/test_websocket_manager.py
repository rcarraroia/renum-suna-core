"""
Testes para o WebSocketManager.

Este módulo contém testes para o WebSocketManager, responsável pela
comunicação em tempo real entre o backend e o frontend.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
from datetime import datetime

from app.services.websocket_manager import WebSocketManager


@pytest.fixture
def mock_redis():
    """
    Mock para o cliente Redis.
    
    Returns:
        MagicMock: Mock para o cliente Redis
    """
    redis_mock = MagicMock()
    redis_mock.publish = AsyncMock()
    redis_mock.pubsub = MagicMock()
    redis_mock.pubsub.return_value.subscribe = AsyncMock()
    redis_mock.pubsub.return_value.get_message = AsyncMock()
    return redis_mock


@pytest.fixture
def websocket_manager(mock_redis):
    """
    Instância do WebSocketManager para testes.
    
    Args:
        mock_redis: Mock para o cliente Redis
        
    Returns:
        WebSocketManager: Instância do WebSocketManager
    """
    return WebSocketManager(mock_redis)


@pytest.fixture
def mock_websocket():
    """
    Mock para o WebSocket.
    
    Returns:
        MagicMock: Mock para o WebSocket
    """
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    return websocket


@pytest.mark.asyncio
async def test_connect(websocket_manager, mock_websocket):
    """
    Testa a conexão de um cliente WebSocket.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
    """
    # Arrange
    user_id = "user123"
    client_info = {"ip": "127.0.0.1", "user_agent": "test-agent"}
    
    # Act
    await websocket_manager.connect(mock_websocket, user_id, client_info)
    
    # Assert
    mock_websocket.accept.assert_called_once()
    assert user_id in websocket_manager.user_connections
    assert mock_websocket in websocket_manager.user_connections[user_id]
    assert mock_websocket in websocket_manager.connection_metadata
    assert websocket_manager.connection_metadata[mock_websocket]["user_id"] == user_id
    assert websocket_manager.connection_metadata[mock_websocket]["client_info"] == client_info


def test_disconnect(websocket_manager, mock_websocket):
    """
    Testa a desconexão de um cliente WebSocket.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
    """
    # Arrange
    user_id = "user123"
    channel = "test_channel"
    
    # Adiciona a conexão
    websocket_manager.user_connections[user_id] = {mock_websocket}
    websocket_manager.active_connections[channel] = {mock_websocket}
    websocket_manager.connection_metadata[mock_websocket] = {
        "user_id": user_id,
        "subscribed_channels": [channel],
        "connected_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "client_info": {}
    }
    
    # Adiciona uma tarefa de heartbeat simulada
    websocket_manager.heartbeat_tasks[mock_websocket] = MagicMock()
    websocket_manager.heartbeat_tasks[mock_websocket].cancel = MagicMock()
    
    # Act
    websocket_manager.disconnect(mock_websocket)
    
    # Assert
    assert user_id not in websocket_manager.user_connections
    assert channel not in websocket_manager.active_connections
    assert mock_websocket not in websocket_manager.connection_metadata
    assert mock_websocket not in websocket_manager.heartbeat_tasks
    websocket_manager.heartbeat_tasks[mock_websocket].cancel.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe(websocket_manager, mock_websocket, mock_redis):
    """
    Testa a inscrição em um canal.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    channel = "test_channel"
    
    # Adiciona a conexão
    websocket_manager.connection_metadata[mock_websocket] = {
        "user_id": user_id,
        "connected_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "client_info": {},
        "subscribed_channels": []
    }
    
    # Act
    await websocket_manager.subscribe(mock_websocket, channel)
    
    # Assert
    assert channel in websocket_manager.connection_metadata[mock_websocket]["subscribed_channels"]
    assert channel in websocket_manager.active_connections
    assert mock_websocket in websocket_manager.active_connections[channel]
    assert channel in websocket_manager.pubsub_tasks


@pytest.mark.asyncio
async def test_send_personal_message(websocket_manager, mock_websocket):
    """
    Testa o envio de mensagem pessoal.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, world!"}
    
    # Adiciona a conexão
    websocket_manager.user_connections[user_id] = {mock_websocket}
    websocket_manager.connection_metadata[mock_websocket] = {
        "user_id": user_id,
        "connected_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "client_info": {},
        "subscribed_channels": []
    }
    
    # Act
    await websocket_manager.send_personal_message(user_id, message)
    
    # Assert
    mock_websocket.send_text.assert_called_once()
    sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
    assert sent_message["type"] == message["type"]
    assert sent_message["content"] == message["content"]
    assert "timestamp" in sent_message


@pytest.mark.asyncio
async def test_broadcast_to_channel(websocket_manager, mock_websocket, mock_redis):
    """
    Testa o broadcast para um canal.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    channel = "test_channel"
    message = {"type": "test", "content": "Hello, channel!"}
    
    # Adiciona a conexão ao canal
    websocket_manager.active_connections[channel] = {mock_websocket}
    websocket_manager.connection_metadata[mock_websocket] = {
        "user_id": "user123",
        "connected_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "client_info": {},
        "subscribed_channels": [channel]
    }
    
    # Act
    await websocket_manager.broadcast_to_channel(channel, message)
    
    # Assert
    mock_redis.publish.assert_called_once_with(channel, json.dumps(message))
    mock_websocket.send_text.assert_called_once()
    sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
    assert sent_message["type"] == message["type"]
    assert sent_message["content"] == message["content"]
    assert "timestamp" in sent_message


@pytest.mark.asyncio
async def test_broadcast_to_all(websocket_manager, mock_websocket, mock_redis):
    """
    Testa o broadcast para todos os usuários.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, everyone!"}
    
    # Adiciona a conexão
    websocket_manager.user_connections[user_id] = {mock_websocket}
    websocket_manager.connection_metadata[mock_websocket] = {
        "user_id": user_id,
        "connected_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "client_info": {},
        "subscribed_channels": []
    }
    
    # Act
    await websocket_manager.broadcast_to_all(message)
    
    # Assert
    mock_redis.publish.assert_called_once_with(websocket_manager.broadcast_channel, json.dumps(message))
    mock_websocket.send_text.assert_called_once()
    sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
    assert sent_message["type"] == message["type"]
    assert sent_message["content"] == message["content"]
    assert "timestamp" in sent_message


@pytest.mark.asyncio
async def test_broadcast_execution_update(websocket_manager, mock_websocket, mock_redis):
    """
    Testa o broadcast de atualização de execução.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    execution_id = "exec123"
    message = {"type": "status_update", "status": "completed"}
    
    # Mock para broadcast_to_channel
    websocket_manager.broadcast_to_channel = AsyncMock()
    
    # Act
    await websocket_manager.broadcast_execution_update(execution_id, message)
    
    # Assert
    expected_channel = f"{websocket_manager.execution_channel_prefix}{execution_id}"
    websocket_manager.broadcast_to_channel.assert_called_once_with(expected_channel, message)


@pytest.mark.asyncio
async def test_send_notification(websocket_manager, mock_websocket, mock_redis):
    """
    Testa o envio de notificação.
    
    Args:
        websocket_manager: Instância do WebSocketManager
        mock_websocket: Mock para o WebSocket
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    notification = {"title": "Test", "message": "This is a test notification"}
    
    # Mock para broadcast_to_channel
    websocket_manager.broadcast_to_channel = AsyncMock()
    
    # Act
    await websocket_manager.send_notification(user_id, notification)
    
    # Assert
    expected_channel = f"{websocket_manager.notification_channel_prefix}{user_id}"
    expected_message = {
        "type": "notification",
        "data": notification
    }
    websocket_manager.broadcast_to_channel.assert_called_once_with(expected_channel, expected_message)