"""
Testes para a integração com o ThreadManager.

Este módulo contém testes para a integração com o ThreadManager do Suna Core,
verificando a extensão do ThreadManager com funcionalidades de equipe.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.services.thread_manager_integration import TeamThreadManagerIntegration
from app.services.team_context_manager import TeamContextManager
from app.services.team_message_bus import TeamMessageBus


@pytest.fixture
def mock_team_context_manager():
    """
    Mock para o gerenciador de contexto compartilhado.
    Returns:
        AsyncMock: Mock para o gerenciador de contexto compartilhado
    """
    mock = AsyncMock()
    mock.get_context = AsyncMock(return_value={})
    mock.update_context = AsyncMock(return_value=True)
    mock.add_message_to_context = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_team_message_bus():
    """
    Mock para o sistema de mensagens entre agentes.
    Returns:
        AsyncMock: Mock para o sistema de mensagens entre agentes
    """
    mock = AsyncMock()
    mock.send_message = AsyncMock(return_value=UUID("00000000-0000-0000-0000-000000000001"))
    mock.broadcast_message = AsyncMock(return_value=UUID("00000000-0000-0000-0000-000000000002"))
    mock.get_messages = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def thread_manager_integration(mock_team_context_manager, mock_team_message_bus):
    """
    Integração com o ThreadManager para testes.
    Args:
        mock_team_context_manager: Mock para o gerenciador de contexto compartilhado
        mock_team_message_bus: Mock para o sistema de mensagens entre agentes
    Returns:
        TeamThreadManagerIntegration: Integração com o ThreadManager
    """
    return TeamThreadManagerIntegration(mock_team_context_manager, mock_team_message_bus)


@pytest.fixture
def mock_thread_manager():
    """
    Mock para o ThreadManager do Suna Core.
    Returns:
        MagicMock: Mock para o ThreadManager
    """
    mock = MagicMock()
    mock.add_message = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_extend_thread_manager(thread_manager_integration, mock_thread_manager):
    """Testa a extensão do ThreadManager com funcionalidades de equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    
    # Act
    await thread_manager_integration.extend_thread_manager(mock_thread_manager, execution_id, agent_id)
    
    # Assert
    assert hasattr(mock_thread_manager, "team_execution_id")
    assert mock_thread_manager.team_execution_id == execution_id
    assert hasattr(mock_thread_manager, "team_agent_id")
    assert mock_thread_manager.team_agent_id == agent_id
    assert hasattr(mock_thread_manager, "team_context_manager")
    assert hasattr(mock_thread_manager, "team_message_bus")


@pytest.mark.asyncio
async def test_extended_add_message(thread_manager_integration, mock_thread_manager, mock_team_context_manager):
    """Testa o método add_message estendido."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    thread_id = "thread-123"
    content = "Test message"
    
    # Estende o ThreadManager
    await thread_manager_integration.extend_thread_manager(mock_thread_manager, execution_id, agent_id)
    
    # Act
    await mock_thread_manager.add_message(thread_id, "text", content, is_llm_message=True)
    
    # Assert
    mock_thread_manager.add_message.assert_called_once()
    mock_team_context_manager.add_message_to_context.assert_called_once()


@pytest.mark.asyncio
async def test_create_team_thread_manager(thread_manager_integration):
    """Testa a criação de um ThreadManager com funcionalidades de equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    
    # Mock para a classe ThreadManager
    mock_thread_manager_class = MagicMock()
    mock_thread_manager_class.return_value = MagicMock()
    
    # Act
    with patch.object(thread_manager_integration, "extend_thread_manager", AsyncMock()) as mock_extend:
        thread_manager = await thread_manager_integration.create_team_thread_manager(
            mock_thread_manager_class,
            execution_id,
            agent_id
        )
    
    # Assert
    mock_thread_manager_class.assert_called_once()
    mock_extend.assert_called_once_with(thread_manager, execution_id, agent_id)


@pytest.mark.asyncio
async def test_get_team_context(thread_manager_integration, mock_team_context_manager):
    """Testa a obtenção do contexto compartilhado da equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    expected_context = {"key": "value"}
    mock_team_context_manager.get_context.return_value = expected_context
    
    # Act
    context = await thread_manager_integration.get_team_context(execution_id)
    
    # Assert
    assert context == expected_context
    mock_team_context_manager.get_context.assert_called_once_with(execution_id)


@pytest.mark.asyncio
async def test_update_team_context(thread_manager_integration, mock_team_context_manager):
    """Testa a atualização do contexto compartilhado da equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    updates = {"key": "value"}
    mock_team_context_manager.update_context.return_value = True
    
    # Act
    result = await thread_manager_integration.update_team_context(execution_id, updates)
    
    # Assert
    assert result is True
    mock_team_context_manager.update_context.assert_called_once_with(execution_id, updates)


@pytest.mark.asyncio
async def test_send_team_message(thread_manager_integration, mock_team_message_bus):
    """Testa o envio de uma mensagem entre agentes da equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    from_agent_id = "agent-123"
    to_agent_id = "agent-456"
    message_type = "info"
    content = {"text": "Hello"}
    expected_message_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_team_message_bus.send_message.return_value = expected_message_id
    
    # Act
    message_id = await thread_manager_integration.send_team_message(
        execution_id,
        from_agent_id,
        to_agent_id,
        message_type,
        content
    )
    
    # Assert
    assert message_id == expected_message_id
    mock_team_message_bus.send_message.assert_called_once_with(
        execution_id=execution_id,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        message_type=message_type,
        content=content
    )


@pytest.mark.asyncio
async def test_get_team_messages(thread_manager_integration, mock_team_message_bus):
    """Testa a obtenção de mensagens da equipe."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    expected_messages = [{"id": 1, "content": "Hello"}]
    mock_team_message_bus.get_messages.return_value = expected_messages
    
    # Act
    messages = await thread_manager_integration.get_team_messages(execution_id, agent_id)
    
    # Assert
    assert messages == expected_messages
    mock_team_message_bus.get_messages.assert_called_once_with(
        execution_id=execution_id,
        agent_id=agent_id,
        limit=100
    )