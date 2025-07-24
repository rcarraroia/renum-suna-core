"""
Testes para o WebSocket de monitoramento em tempo real.

Este módulo contém testes para o WebSocket de monitoramento em tempo real
de execuções de equipes.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.main import app
from app.services.websocket_manager import WebSocketManager


@pytest.fixture
def client():
    """
    Cliente de teste para a API.
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


@pytest.fixture
def mock_websocket_manager():
    """
    Mock para o gerenciador de WebSockets.
    Returns:
        MagicMock: Mock para o gerenciador de WebSockets
    """
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = MagicMock()
    mock.broadcast = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_websocket_manager_connect():
    """Testa a conexão de um cliente WebSocket."""
    # Arrange
    manager = WebSocketManager()
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    # Act
    await manager.connect(websocket, execution_id)
    
    # Assert
    websocket.accept.assert_called_once()
    assert execution_id in manager.active_connections
    assert websocket in manager.active_connections[execution_id]


@pytest.mark.asyncio
async def test_websocket_manager_disconnect():
    """Testa a desconexão de um cliente WebSocket."""
    # Arrange
    manager = WebSocketManager()
    websocket = MagicMock()
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    # Adiciona a conexão
    manager.active_connections[execution_id] = {websocket}
    
    # Act
    manager.disconnect(websocket, execution_id)
    
    # Assert
    assert execution_id not in manager.active_connections


@pytest.mark.asyncio
async def test_websocket_manager_broadcast():
    """Testa o broadcast de mensagens para clientes WebSocket."""
    # Arrange
    manager = WebSocketManager()
    websocket1 = MagicMock()
    websocket1.send_text = AsyncMock()
    websocket2 = MagicMock()
    websocket2.send_text = AsyncMock()
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    # Adiciona as conexões
    manager.active_connections[execution_id] = {websocket1, websocket2}
    
    # Act
    message = {"type": "status_update", "data": {"status": "running"}}
    await manager.broadcast(execution_id, message)
    
    # Assert
    websocket1.send_text.assert_called_once()
    websocket2.send_text.assert_called_once()
    
    # Verifica se a mensagem enviada contém os dados corretos
    sent_message = json.loads(websocket1.send_text.call_args[0][0])
    assert sent_message["type"] == "status_update"
    assert sent_message["data"]["status"] == "running"
    assert "timestamp" in sent_message


@pytest.mark.asyncio
async def test_websocket_manager_broadcast_error_handling():
    """Testa o tratamento de erros no broadcast de mensagens."""
    # Arrange
    manager = WebSocketManager()
    websocket1 = MagicMock()
    websocket1.send_text = AsyncMock()
    websocket2 = MagicMock()
    websocket2.send_text = AsyncMock(side_effect=Exception("Connection error"))
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    # Adiciona as conexões
    manager.active_connections[execution_id] = {websocket1, websocket2}
    
    # Act
    message = {"type": "status_update", "data": {"status": "running"}}
    await manager.broadcast(execution_id, message)
    
    # Assert
    websocket1.send_text.assert_called_once()
    websocket2.send_text.assert_called_once()
    
    # Verifica se a conexão com erro foi removida
    assert websocket1 in manager.active_connections[execution_id]
    assert websocket2 not in manager.active_connections[execution_id]