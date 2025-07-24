"""
Testes para as ferramentas de equipe.

Este módulo contém testes para as ferramentas de contexto compartilhado e
mensagens entre agentes da equipe.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.services.team_context_tool import TeamContextTool
from app.services.team_message_tool import TeamMessageTool


@pytest.fixture
def mock_team_context_manager():
    """
    Mock para o gerenciador de contexto compartilhado.
    Returns:
        AsyncMock: Mock para o gerenciador de contexto compartilhado
    """
    mock = AsyncMock()
    mock.get_context = AsyncMock(return_value={"key": "value"})
    mock.get_variable = AsyncMock(return_value="value")
    mock.set_variable = AsyncMock(return_value=True)
    mock.delete_variable = AsyncMock(return_value=True)
    mock.add_message_to_context = AsyncMock(return_value=True)
    mock.get_messages = AsyncMock(return_value=[{"id": 1, "content": "Hello"}])
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
    mock.request_response = AsyncMock(return_value={"response": "Hello"})
    mock.get_messages = AsyncMock(return_value=[{"id": 1, "content": "Hello"}])
    mock.respond_to_request = AsyncMock(return_value=UUID("00000000-0000-0000-0000-000000000003"))
    return mock


@pytest.fixture
def context_tool(mock_team_context_manager):
    """
    Ferramenta de contexto compartilhado para testes.
    Args:
        mock_team_context_manager: Mock para o gerenciador de contexto compartilhado
    Returns:
        TeamContextTool: Ferramenta de contexto compartilhado
    """
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    return TeamContextTool(mock_team_context_manager, execution_id, agent_id)


@pytest.fixture
def message_tool(mock_team_message_bus):
    """
    Ferramenta de mensagens da equipe para testes.
    Args:
        mock_team_message_bus: Mock para o sistema de mensagens entre agentes
    Returns:
        TeamMessageTool: Ferramenta de mensagens da equipe
    """
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    return TeamMessageTool(mock_team_message_bus, execution_id, agent_id)


@pytest.mark.asyncio
async def test_context_tool_get_context(context_tool, mock_team_context_manager):
    """Testa a obtenção do contexto compartilhado."""
    # Act
    context = await context_tool.get_context()
    
    # Assert
    assert context == {"key": "value"}
    mock_team_context_manager.get_context.assert_called_once_with(context_tool.execution_id)


@pytest.mark.asyncio
async def test_context_tool_get_variable(context_tool, mock_team_context_manager):
    """Testa a obtenção de uma variável do contexto compartilhado."""
    # Act
    value = await context_tool.get_variable("key")
    
    # Assert
    assert value == "value"
    mock_team_context_manager.get_variable.assert_called_once_with(context_tool.execution_id, "key")


@pytest.mark.asyncio
async def test_context_tool_set_variable(context_tool, mock_team_context_manager):
    """Testa a definição de uma variável no contexto compartilhado."""
    # Act
    result = await context_tool.set_variable("key", "value")
    
    # Assert
    assert result is True
    mock_team_context_manager.set_variable.assert_called_once_with(
        context_tool.execution_id, "key", "value", context_tool.agent_id
    )


@pytest.mark.asyncio
async def test_context_tool_delete_variable(context_tool, mock_team_context_manager):
    """Testa a remoção de uma variável do contexto compartilhado."""
    # Act
    result = await context_tool.delete_variable("key")
    
    # Assert
    assert result is True
    mock_team_context_manager.delete_variable.assert_called_once_with(
        context_tool.execution_id, "key", context_tool.agent_id
    )


@pytest.mark.asyncio
async def test_context_tool_add_message_to_context(context_tool, mock_team_context_manager):
    """Testa a adição de uma mensagem ao contexto compartilhado."""
    # Act
    result = await context_tool.add_message_to_context("user", "Hello")
    
    # Assert
    assert result is True
    mock_team_context_manager.add_message_to_context.assert_called_once_with(
        context_tool.execution_id, context_tool.agent_id, "user", "Hello"
    )


@pytest.mark.asyncio
async def test_context_tool_get_messages(context_tool, mock_team_context_manager):
    """Testa a obtenção de mensagens do contexto compartilhado."""
    # Act
    messages = await context_tool.get_messages()
    
    # Assert
    assert messages == [{"id": 1, "content": "Hello"}]
    mock_team_context_manager.get_messages.assert_called_once_with(
        context_tool.execution_id, 10, None, None
    )


@pytest.mark.asyncio
async def test_message_tool_send_message(message_tool, mock_team_message_bus):
    """Testa o envio de uma mensagem para outro agente."""
    # Act
    message_id = await message_tool.send_message("agent-456", "info", {"text": "Hello"})
    
    # Assert
    assert message_id == "00000000-0000-0000-0000-000000000001"
    mock_team_message_bus.send_message.assert_called_once_with(
        execution_id=message_tool.execution_id,
        from_agent_id=message_tool.agent_id,
        to_agent_id="agent-456",
        message_type="info",
        content={"text": "Hello"}
    )


@pytest.mark.asyncio
async def test_message_tool_broadcast_message(message_tool, mock_team_message_bus):
    """Testa o envio de uma mensagem para todos os agentes."""
    # Act
    message_id = await message_tool.broadcast_message("info", {"text": "Hello"})
    
    # Assert
    assert message_id == "00000000-0000-0000-0000-000000000002"
    mock_team_message_bus.broadcast_message.assert_called_once_with(
        execution_id=message_tool.execution_id,
        from_agent_id=message_tool.agent_id,
        message_type="info",
        content={"text": "Hello"}
    )


@pytest.mark.asyncio
async def test_message_tool_request_response(message_tool, mock_team_message_bus):
    """Testa o envio de uma mensagem e aguardo de resposta."""
    # Act
    response = await message_tool.request_response("agent-456", "info", {"text": "Hello"})
    
    # Assert
    assert response == {"response": "Hello"}
    mock_team_message_bus.request_response.assert_called_once_with(
        execution_id=message_tool.execution_id,
        from_agent_id=message_tool.agent_id,
        to_agent_id="agent-456",
        message_type="info",
        content={"text": "Hello"},
        timeout=60
    )


@pytest.mark.asyncio
async def test_message_tool_get_messages(message_tool, mock_team_message_bus):
    """Testa a obtenção de mensagens recebidas pelo agente."""
    # Act
    messages = await message_tool.get_messages()
    
    # Assert
    assert messages == [{"id": 1, "content": "Hello"}]
    mock_team_message_bus.get_messages.assert_called_once_with(
        execution_id=message_tool.execution_id,
        agent_id=message_tool.agent_id,
        limit=10,
        from_agent_id=None,
        message_type=None
    )


@pytest.mark.asyncio
async def test_message_tool_respond_to_request(message_tool, mock_team_message_bus):
    """Testa a resposta a uma solicitação de outro agente."""
    # Act
    message_id = await message_tool.respond_to_request("00000000-0000-0000-0000-000000000001", {"text": "Hello"})
    
    # Assert
    assert message_id == "00000000-0000-0000-0000-000000000003"
    mock_team_message_bus.respond_to_request.assert_called_once_with(
        execution_id=message_tool.execution_id,
        request_message_id=UUID("00000000-0000-0000-0000-000000000001"),
        from_agent_id=message_tool.agent_id,
        content={"text": "Hello"}
    )