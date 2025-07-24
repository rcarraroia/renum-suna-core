"""
Testes para as rotas WebSocket.

Este módulo contém testes para as rotas WebSocket, responsáveis pela
comunicação em tempo real entre o backend e o frontend.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.main import app


@pytest.fixture
def client():
    """
    Cliente de teste para a aplicação FastAPI.
    
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """
    Mock para a autenticação.
    
    Returns:
        MagicMock: Mock para a autenticação
    """
    with patch("app.core.auth.get_user_id_from_token", return_value="user123"):
        yield


@pytest.fixture
def mock_websocket_manager():
    """
    Mock para o gerenciador de WebSockets.
    
    Returns:
        MagicMock: Mock para o gerenciador de WebSockets
    """
    manager = MagicMock()
    manager.connect = AsyncMock()
    manager.disconnect = MagicMock()
    manager.subscribe = AsyncMock()
    manager.unsubscribe = AsyncMock()
    manager.send_personal_message = AsyncMock()
    manager.broadcast_to_channel = AsyncMock()
    manager.broadcast_to_all = AsyncMock()
    manager.get_connection_stats = MagicMock(return_value={"total_connections": 1, "active_users": 1})
    
    with patch("app.api.routes.websocket.get_websocket_manager", return_value=manager):
        yield manager


@pytest.fixture
def mock_team_orchestrator():
    """
    Mock para o orquestrador de equipes.
    
    Returns:
        MagicMock: Mock para o orquestrador de equipes
    """
    orchestrator = MagicMock()
    orchestrator.get_execution_status = AsyncMock(return_value={"status": "running", "progress": 50})
    orchestrator.get_execution_logs = AsyncMock(return_value=[{"timestamp": "2023-01-01T00:00:00", "message": "Test log"}])
    orchestrator.stop_execution = AsyncMock(return_value=True)
    
    with patch("app.api.routes.websocket.get_team_orchestrator", return_value=orchestrator):
        yield orchestrator


def test_websocket_auth_connection_success(client, mock_auth, mock_websocket_manager):
    """
    Testa a conexão bem-sucedida ao WebSocket de autenticação.
    
    Args:
        client: Cliente de teste
        mock_auth: Mock para a autenticação
        mock_websocket_manager: Mock para o gerenciador de WebSockets
    """
    with client.websocket_connect("/api/v1/ws/auth?token=valid_token") as websocket:
        # Simula recebimento de mensagem de boas-vindas
        data = {"type": "connection_established", "user_id": "user123"}
        websocket.send_json(data)
        
        # Simula comando ping
        websocket.send_json({"command": "ping", "data": "test"})
        
        # Simula comando subscribe
        websocket.send_json({"command": "subscribe", "channel": "test_channel"})
        
        # Simula comando unsubscribe
        websocket.send_json({"command": "unsubscribe", "channel": "test_channel"})
    
    # Verifica se os métodos foram chamados
    mock_websocket_manager.connect.assert_called_once()
    mock_websocket_manager.subscribe.assert_called_once()
    mock_websocket_manager.unsubscribe.assert_called_once()


def test_websocket_auth_invalid_token(client):
    """
    Testa a conexão ao WebSocket de autenticação com token inválido.
    
    Args:
        client: Cliente de teste
    """
    with patch("app.core.auth.get_user_id_from_token", return_value=None):
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/api/v1/ws/auth?token=invalid_token"):
                pass


def test_websocket_execution_monitor_success(client, mock_auth, mock_websocket_manager, mock_team_orchestrator):
    """
    Testa a conexão bem-sucedida ao WebSocket de monitoramento de execução.
    
    Args:
        client: Cliente de teste
        mock_auth: Mock para a autenticação
        mock_websocket_manager: Mock para o gerenciador de WebSockets
        mock_team_orchestrator: Mock para o orquestrador de equipes
    """
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    with client.websocket_connect(f"/api/v1/ws/executions/{execution_id}?token=valid_token") as websocket:
        # Simula recebimento de status inicial
        data = {"type": "status_update", "data": {"status": "running", "progress": 50}}
        websocket.send_json(data)
        
        # Simula comando get_logs
        websocket.send_json({"command": "get_logs", "limit": 10, "offset": 0})
        
        # Simula comando stop_execution
        websocket.send_json({"command": "stop_execution"})
    
    # Verifica se os métodos foram chamados
    mock_websocket_manager.connect.assert_called_once()
    mock_websocket_manager.subscribe.assert_called_once()
    mock_team_orchestrator.get_execution_status.assert_called_once()
    mock_team_orchestrator.get_execution_logs.assert_called_once()
    mock_team_orchestrator.stop_execution.assert_called_once()


def test_websocket_execution_monitor_not_found(client, mock_auth, mock_team_orchestrator):
    """
    Testa a conexão ao WebSocket de monitoramento para uma execução inexistente.
    
    Args:
        client: Cliente de teste
        mock_auth: Mock para a autenticação
        mock_team_orchestrator: Mock para o orquestrador de equipes
    """
    execution_id = "00000000-0000-0000-0000-000000000001"
    
    # Configura o mock para retornar None (execução não encontrada)
    mock_team_orchestrator.get_execution_status.return_value = None
    
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/api/v1/ws/executions/{execution_id}?token=valid_token"):
            pass


def test_websocket_admin_success(client, mock_auth, mock_websocket_manager):
    """
    Testa a conexão bem-sucedida ao WebSocket de administração.
    
    Args:
        client: Cliente de teste
        mock_auth: Mock para a autenticação
        mock_websocket_manager: Mock para o gerenciador de WebSockets
    """
    with client.websocket_connect("/api/v1/ws/admin?token=valid_token") as websocket:
        # Simula recebimento de estatísticas iniciais
        data = {"type": "stats", "data": {"total_connections": 1, "active_users": 1}}
        websocket.send_json(data)
        
        # Simula comando get_stats
        websocket.send_json({"command": "get_stats"})
        
        # Simula comando broadcast
        websocket.send_json({
            "command": "broadcast",
            "message": "Test message",
            "target_users": ["user1", "user2"]
        })
        
        # Simula comando disconnect_user
        websocket.send_json({
            "command": "disconnect_user",
            "user_id": "user1"
        })
    
    # Verifica se os métodos foram chamados
    mock_websocket_manager.connect.assert_called_once()
    mock_websocket_manager.subscribe.assert_called_once()
    mock_websocket_manager.get_connection_stats.assert_called()
    mock_websocket_manager.send_personal_message.assert_called()