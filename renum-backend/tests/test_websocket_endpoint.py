"""
Testes para o endpoint WebSocket de monitoramento em tempo real.

Este módulo contém testes para o endpoint WebSocket de monitoramento em tempo real
de execuções de equipes.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from uuid import UUID

from app.main import app
from app.models.team_models import TeamExecutionStatus, ExecutionStatus


@pytest.fixture
def client():
    """
    Cliente de teste para a API.
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """
    Mock para autenticação.
    Returns:
        MagicMock: Mock para autenticação
    """
    with patch("app.core.auth.get_current_user_id", return_value=UUID("00000000-0000-0000-0000-000000000001")), \
         patch("app.core.auth.get_user_id_from_token", return_value=UUID("00000000-0000-0000-0000-000000000001")):
        yield


@pytest.fixture
def mock_team_orchestrator():
    """
    Mock para o orquestrador de equipes.
    Returns:
        MagicMock: Mock para o orquestrador de equipes
    """
    mock = MagicMock()
    mock.get_execution_status = AsyncMock()
    mock.subscribe_to_execution_updates = AsyncMock()
    mock.unsubscribe_from_execution_updates = AsyncMock()
    return mock


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


def test_websocket_connection_success(client, mock_auth, mock_team_orchestrator):
    """Testa a conexão bem-sucedida ao WebSocket."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para retornar o status da execução
    status = TeamExecutionStatus(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.RUNNING,
        progress=50.0,
        current_step=2,
        total_steps=3,
        active_agents=["agent-456"],
        completed_agents=["agent-123"],
        failed_agents=[],
        updated_at="2023-01-01T00:02:30Z"
    )
    mock_team_orchestrator.get_execution_status.return_value = status
    
    # Configura o mock para retornar atualizações
    async def mock_updates():
        yield {"type": "status_update", "data": {"status": "running"}}
        yield {"type": "status_update", "data": {"status": "completed"}}
    
    mock_team_orchestrator.subscribe_to_execution_updates.return_value = mock_updates()
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator), \
         patch("app.services.websocket_manager.websocket_manager.connect", AsyncMock()), \
         patch("app.services.websocket_manager.websocket_manager.disconnect", MagicMock()):
        # Act & Assert
        with client.websocket_connect(f"/api/v1/ws/executions/{execution_id}/monitor?token=valid_token") as websocket:
            # Verifica se recebeu a primeira atualização
            data = websocket.receive_json()
            assert data["type"] == "status_update"
            
            # Verifica se recebeu a segunda atualização
            data = websocket.receive_json()
            assert data["type"] == "status_update"
            assert data["data"]["status"] == "completed"


def test_websocket_connection_invalid_token(client, mock_auth, mock_team_orchestrator):
    """Testa a conexão ao WebSocket com token inválido."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar None (token inválido)
    with patch("app.core.auth.get_user_id_from_token", return_value=None):
        # Act & Assert
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect(f"/api/v1/ws/executions/{execution_id}/monitor?token=invalid_token"):
                pass
        
        assert excinfo.value.code == 1008  # Código de erro para token inválido


def test_websocket_connection_execution_not_found(client, mock_auth, mock_team_orchestrator):
    """Testa a conexão ao WebSocket para uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar None (execução não encontrada)
    mock_team_orchestrator.get_execution_status.return_value = None
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act & Assert
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect(f"/api/v1/ws/executions/{execution_id}/monitor?token=valid_token"):
                pass
        
        assert excinfo.value.code == 1008  # Código de erro para execução não encontrada