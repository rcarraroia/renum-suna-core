"""
Testes para o WebSocketChannelService.

Este módulo contém testes para o WebSocketChannelService, responsável pelo
gerenciamento de canais e salas WebSocket.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.websocket_channel_service import WebSocketChannelService


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
    redis_mock.hset = AsyncMock()
    redis_mock.sadd = AsyncMock()
    redis_mock.srem = AsyncMock()
    redis_mock.smembers = AsyncMock(return_value=[b"user1", b"user2"])
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
def channel_service(mock_redis, mock_repository):
    """
    Instância do WebSocketChannelService para testes.
    
    Args:
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
        
    Returns:
        WebSocketChannelService: Instância do WebSocketChannelService
    """
    return WebSocketChannelService(mock_redis, mock_repository)


@pytest.mark.asyncio
async def test_create_channel(channel_service, mock_redis):
    """
    Testa a criação de um canal.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    channel_name = "test_channel"
    metadata = {"description": "Test channel"}
    
    # Act
    result = await channel_service.create_channel(channel_name, metadata)
    
    # Assert
    assert result == f"{channel_service.channel_prefix}{channel_name}"
    mock_redis.hset.assert_called_once()
    assert channel_name in str(mock_redis.hset.call_args)
    assert "description" in str(mock_redis.hset.call_args)


@pytest.mark.asyncio
async def test_create_room(channel_service, mock_redis):
    """
    Testa a criação de uma sala.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    room_name = "test_room"
    metadata = {"description": "Test room"}
    
    # Act
    result = await channel_service.create_room(room_name, metadata)
    
    # Assert
    assert result == f"{channel_service.room_prefix}{room_name}"
    mock_redis.hset.assert_called_once()
    assert room_name in str(mock_redis.hset.call_args)
    assert "description" in str(mock_redis.hset.call_args)


@pytest.mark.asyncio
async def test_subscribe_to_channel(channel_service, mock_redis):
    """
    Testa a inscrição em um canal.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    channel_name = "test_channel"
    user_id = "user123"
    
    # Act
    result = await channel_service.subscribe_to_channel(channel_name, user_id)
    
    # Assert
    assert result is True
    mock_redis.sadd.assert_called()
    assert f"{channel_service.channel_prefix}{channel_name}:subscribers" in str(mock_redis.sadd.call_args_list[0])
    assert user_id in str(mock_redis.sadd.call_args_list[0])
    assert f"{channel_service.user_prefix}{user_id}:subscriptions" in str(mock_redis.sadd.call_args_list[1])


@pytest.mark.asyncio
async def test_unsubscribe_from_channel(channel_service, mock_redis):
    """
    Testa o cancelamento de inscrição em um canal.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    channel_name = "test_channel"
    user_id = "user123"
    full_channel = f"{channel_service.channel_prefix}{channel_name}"
    
    # Adiciona o canal à lista de assinantes
    channel_service.channel_subscribers[full_channel] = {user_id}
    
    # Act
    result = await channel_service.unsubscribe_from_channel(channel_name, user_id)
    
    # Assert
    assert result is True
    mock_redis.srem.assert_called()
    assert f"{channel_service.channel_prefix}{channel_name}:subscribers" in str(mock_redis.srem.call_args_list[0])
    assert user_id in str(mock_redis.srem.call_args_list[0])
    assert f"{channel_service.user_prefix}{user_id}:subscriptions" in str(mock_redis.srem.call_args_list[1])
    assert full_channel not in channel_service.channel_subscribers


@pytest.mark.asyncio
async def test_join_room(channel_service, mock_redis):
    """
    Testa a entrada em uma sala.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    room_name = "test_room"
    user_id = "user123"
    
    # Mock para publish_to_room
    channel_service.publish_to_room = AsyncMock()
    
    # Act
    result = await channel_service.join_room(room_name, user_id)
    
    # Assert
    assert result is True
    mock_redis.sadd.assert_called()
    assert f"{channel_service.room_prefix}{room_name}:members" in str(mock_redis.sadd.call_args_list[0])
    assert user_id in str(mock_redis.sadd.call_args_list[0])
    assert f"{channel_service.user_prefix}{user_id}:rooms" in str(mock_redis.sadd.call_args_list[1])
    channel_service.publish_to_room.assert_called_once()
    assert room_name in str(channel_service.publish_to_room.call_args)
    assert "join" in str(channel_service.publish_to_room.call_args)


@pytest.mark.asyncio
async def test_leave_room(channel_service, mock_redis):
    """
    Testa a saída de uma sala.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    room_name = "test_room"
    user_id = "user123"
    full_room = f"{channel_service.room_prefix}{room_name}"
    
    # Adiciona a sala à lista de membros
    channel_service.room_members[full_room] = {user_id}
    
    # Mock para publish_to_room
    channel_service.publish_to_room = AsyncMock()
    
    # Act
    result = await channel_service.leave_room(room_name, user_id)
    
    # Assert
    assert result is True
    mock_redis.srem.assert_called()
    assert f"{channel_service.room_prefix}{room_name}:members" in str(mock_redis.srem.call_args_list[0])
    assert user_id in str(mock_redis.srem.call_args_list[0])
    assert f"{channel_service.user_prefix}{user_id}:rooms" in str(mock_redis.srem.call_args_list[1])
    channel_service.publish_to_room.assert_called_once()
    assert room_name in str(channel_service.publish_to_room.call_args)
    assert "leave" in str(channel_service.publish_to_room.call_args)
    assert full_room not in channel_service.room_members


@pytest.mark.asyncio
async def test_publish_to_channel(channel_service, mock_redis, mock_repository):
    """
    Testa a publicação em um canal.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
    """
    # Arrange
    channel_name = "test_channel"
    message = {"type": "test", "content": "Hello, channel!"}
    
    # Act
    result = await channel_service.publish_to_channel(channel_name, message)
    
    # Assert
    assert result is True
    mock_redis.publish.assert_called_once()
    assert f"{channel_service.channel_prefix}{channel_name}" in str(mock_redis.publish.call_args)
    assert "Hello, channel!" in str(mock_redis.publish.call_args)
    mock_repository.log_message.assert_called_once()
    assert channel_name in str(mock_repository.log_message.call_args)
    assert "Hello, channel!" in str(mock_repository.log_message.call_args)


@pytest.mark.asyncio
async def test_publish_to_room(channel_service, mock_redis, mock_repository):
    """
    Testa a publicação em uma sala.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
    """
    # Arrange
    room_name = "test_room"
    message = {"type": "test", "content": "Hello, room!"}
    
    # Act
    result = await channel_service.publish_to_room(room_name, message)
    
    # Assert
    assert result is True
    mock_redis.publish.assert_called_once()
    assert f"{channel_service.room_prefix}{room_name}" in str(mock_redis.publish.call_args)
    assert "Hello, room!" in str(mock_redis.publish.call_args)
    mock_repository.log_message.assert_called_once()
    assert room_name in str(mock_repository.log_message.call_args)
    assert "Hello, room!" in str(mock_repository.log_message.call_args)


@pytest.mark.asyncio
async def test_publish_to_user(channel_service, mock_redis, mock_repository):
    """
    Testa a publicação para um usuário.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
    """
    # Arrange
    user_id = "user123"
    message = {"type": "test", "content": "Hello, user!"}
    
    # Act
    result = await channel_service.publish_to_user(user_id, message)
    
    # Assert
    assert result is True
    mock_redis.publish.assert_called_once()
    assert f"{channel_service.user_prefix}{user_id}" in str(mock_redis.publish.call_args)
    assert "Hello, user!" in str(mock_redis.publish.call_args)
    mock_repository.log_message.assert_called_once()
    assert user_id in str(mock_repository.log_message.call_args)
    assert "Hello, user!" in str(mock_repository.log_message.call_args)


@pytest.mark.asyncio
async def test_broadcast(channel_service, mock_redis, mock_repository):
    """
    Testa o broadcast para todos os usuários.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
        mock_repository: Mock para o repositório WebSocket
    """
    # Arrange
    message = {"type": "test", "content": "Hello, everyone!"}
    exclude_users = ["user1", "user2"]
    
    # Act
    result = await channel_service.broadcast(message, exclude_users)
    
    # Assert
    assert result is True
    mock_redis.publish.assert_called_once()
    assert channel_service.broadcast_channel in str(mock_redis.publish.call_args)
    assert "Hello, everyone!" in str(mock_redis.publish.call_args)
    assert "exclude_users" in str(mock_redis.publish.call_args)
    mock_repository.log_message.assert_called_once()
    assert "broadcast" in str(mock_repository.log_message.call_args)
    assert "Hello, everyone!" in str(mock_repository.log_message.call_args)
    assert "exclude_users" in str(mock_repository.log_message.call_args)


@pytest.mark.asyncio
async def test_get_channel_subscribers(channel_service, mock_redis):
    """
    Testa a obtenção de assinantes de um canal.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    channel_name = "test_channel"
    mock_redis.smembers.return_value = [b"user1", b"user2"]
    
    # Act
    result = await channel_service.get_channel_subscribers(channel_name)
    
    # Assert
    assert len(result) == 2
    assert "user1" in result
    assert "user2" in result
    mock_redis.smembers.assert_called_once()
    assert f"{channel_service.channel_prefix}{channel_name}:subscribers" in str(mock_redis.smembers.call_args)


@pytest.mark.asyncio
async def test_get_room_members(channel_service, mock_redis):
    """
    Testa a obtenção de membros de uma sala.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    room_name = "test_room"
    mock_redis.smembers.return_value = [b"user1", b"user2"]
    
    # Act
    result = await channel_service.get_room_members(room_name)
    
    # Assert
    assert len(result) == 2
    assert "user1" in result
    assert "user2" in result
    mock_redis.smembers.assert_called_once()
    assert f"{channel_service.room_prefix}{room_name}:members" in str(mock_redis.smembers.call_args)


@pytest.mark.asyncio
async def test_get_user_subscriptions(channel_service, mock_redis):
    """
    Testa a obtenção de inscrições de um usuário.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    mock_redis.smembers.return_value = [
        f"{channel_service.channel_prefix}channel1".encode(),
        f"{channel_service.channel_prefix}channel2".encode()
    ]
    
    # Act
    result = await channel_service.get_user_subscriptions(user_id)
    
    # Assert
    assert len(result) == 2
    assert "channel1" in result
    assert "channel2" in result
    mock_redis.smembers.assert_called_once()
    assert f"{channel_service.user_prefix}{user_id}:subscriptions" in str(mock_redis.smembers.call_args)


@pytest.mark.asyncio
async def test_get_user_rooms(channel_service, mock_redis):
    """
    Testa a obtenção de salas de um usuário.
    
    Args:
        channel_service: Instância do WebSocketChannelService
        mock_redis: Mock para o cliente Redis
    """
    # Arrange
    user_id = "user123"
    mock_redis.smembers.return_value = [
        f"{channel_service.room_prefix}room1".encode(),
        f"{channel_service.room_prefix}room2".encode()
    ]
    
    # Act
    result = await channel_service.get_user_rooms(user_id)
    
    # Assert
    assert len(result) == 2
    assert "room1" in result
    assert "room2" in result
    mock_redis.smembers.assert_called_once()
    assert f"{channel_service.user_prefix}{user_id}:rooms" in str(mock_redis.smembers.call_args)


def test_register_message_handler(channel_service):
    """
    Testa o registro de um handler de mensagem.
    
    Args:
        channel_service: Instância do WebSocketChannelService
    """
    # Arrange
    message_type = "test_type"
    handler = AsyncMock()
    
    # Act
    channel_service.register_message_handler(message_type, handler)
    
    # Assert
    assert message_type in channel_service.message_handlers
    assert handler in channel_service.message_handlers[message_type]