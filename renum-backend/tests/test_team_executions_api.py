"""
Testes para a API de execuções de equipes.

Este módulo contém testes para os endpoints da API de execuções de equipes,
verificando a execução, monitoramento e controle de execuções.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from app.main import app
from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    TeamExecutionStatus,
    TeamExecutionResult,
    ExecutionLogEntry,
    ExecutionStatus,
    PaginatedResponse
)


@pytest.fixture
def client():
    """
    Cliente de teste para a API.
    
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


@pytest.mark.asyncio
async def test_execute_team_success(client, mock_auth, mock_team_orchestrator, mock_team_execution_repository):
    """Testa a execução bem-sucedida de uma equipe."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar 0 execuções ativas (abaixo do limite)
    mock_team_execution_repository.count_active_executions.return_value = 0
    
    # Configura o mock para retornar uma execução criada
    execution_response = TeamExecutionResponse(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.PENDING,
        created_at="2023-01-01T00:00:00Z"
    )
    mock_team_orchestrator.execute_team.return_value = execution_response
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator), \
         patch("app.core.dependencies.get_team_execution_repository", return_value=mock_team_execution_repository):
        # Act
        response = client.post(
            f"/api/v1/teams/{team_id}/execute",
            json={
                "team_id": str(team_id),
                "initial_prompt": "Test prompt"
            }
        )
        
        # Assert
        assert response.status_code == 200
        mock_team_execution_repository.count_active_executions.assert_called_once()
        mock_team_orchestrator.execute_team.assert_called_once()
        assert response.json()["execution_id"] == str(execution_id)
        assert response.json()["status"] == ExecutionStatus.PENDING.value


@pytest.mark.asyncio
async def test_execute_team_exceeds_limit(client, mock_auth, mock_team_orchestrator, mock_team_execution_repository):
    """Testa a execução de uma equipe quando o limite de execuções ativas é excedido."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para retornar 5 execuções ativas (no limite)
    mock_team_execution_repository.count_active_executions.return_value = 5
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator), \
         patch("app.core.dependencies.get_team_execution_repository", return_value=mock_team_execution_repository), \
         patch("app.core.validators.get_settings", return_value=MagicMock(MAX_CONCURRENT_EXECUTIONS=5)):
        # Act
        response = client.post(
            f"/api/v1/teams/{team_id}/execute",
            json={
                "team_id": str(team_id),
                "initial_prompt": "Test prompt"
            }
        )
        
        # Assert
        assert response.status_code == 400
        mock_team_execution_repository.count_active_executions.assert_called_once()
        mock_team_orchestrator.execute_team.assert_not_called()
        assert "Maximum number of concurrent executions reached" in response.json()["detail"]


@pytest.mark.asyncio
async def test_execute_team_mismatched_ids(client, mock_auth, mock_team_orchestrator):
    """Testa a execução de uma equipe com IDs incompatíveis."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    wrong_team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.post(
            f"/api/v1/teams/{team_id}/execute",
            json={
                "team_id": str(wrong_team_id),
                "initial_prompt": "Test prompt"
            }
        )
        
        # Assert
        assert response.status_code == 400
        mock_team_orchestrator.execute_team.assert_not_called()
        assert "Team ID in path does not match" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_execution_status_success(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção bem-sucedida do status de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    
    # Configura o mock para retornar o status da execução
    execution_status = TeamExecutionStatus(
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
    mock_team_orchestrator.get_execution_status.return_value = execution_status
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/status")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.get_execution_status.assert_called_once_with(execution_id, user_id)
        assert response.json()["execution_id"] == str(execution_id)
        assert response.json()["status"] == ExecutionStatus.RUNNING.value
        assert response.json()["progress"] == 50.0


@pytest.mark.asyncio
async def test_get_execution_status_not_found(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção do status de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar None (execução não encontrada)
    mock_team_orchestrator.get_execution_status.return_value = None
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/status")
        
        # Assert
        assert response.status_code == 404
        mock_team_orchestrator.get_execution_status.assert_called_once()
        assert f"Execution {execution_id} not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_execution_result_success(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção bem-sucedida do resultado de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    
    # Configura o mock para retornar o resultado da execução
    execution_result = TeamExecutionResult(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.COMPLETED,
        final_result={"summary": "Test result"},
        agent_results={
            "agent-123": {"result": "Agent 123 result"},
            "agent-456": {"result": "Agent 456 result"},
            "agent-789": {"result": "Agent 789 result"}
        },
        started_at="2023-01-01T00:00:00Z",
        completed_at="2023-01-01T00:05:00Z",
        execution_duration=300
    )
    mock_team_orchestrator.get_execution_result.return_value = execution_result
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/result")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.get_execution_result.assert_called_once_with(execution_id, user_id)
        assert response.json()["execution_id"] == str(execution_id)
        assert response.json()["status"] == ExecutionStatus.COMPLETED.value
        assert response.json()["final_result"] == {"summary": "Test result"}


@pytest.mark.asyncio
async def test_get_execution_result_not_found(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção do resultado de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar None (execução não encontrada)
    mock_team_orchestrator.get_execution_result.return_value = None
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/result")
        
        # Assert
        assert response.status_code == 404
        mock_team_orchestrator.get_execution_result.assert_called_once()
        assert f"Execution {execution_id} not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_execution_result_not_completed(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção do resultado de uma execução que ainda não foi concluída."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para retornar uma execução em andamento
    execution_result = TeamExecutionResult(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.RUNNING,
        final_result=None,
        agent_results={},
        started_at="2023-01-01T00:00:00Z",
        completed_at=None,
        execution_duration=None
    )
    mock_team_orchestrator.get_execution_result.return_value = execution_result
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/result")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.get_execution_result.assert_called_once()
        assert response.json()["status"] == ExecutionStatus.RUNNING.value
        assert response.json()["final_result"] is None


@pytest.mark.asyncio
async def test_stop_execution_success(client, mock_auth, mock_team_orchestrator):
    """Testa a parada bem-sucedida de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    
    # Configura o mock para retornar True (execução parada com sucesso)
    mock_team_orchestrator.stop_execution.return_value = True
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.post(f"/api/v1/executions/{execution_id}/stop")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.stop_execution.assert_called_once_with(execution_id, user_id)
        assert response.json()["status"] == "success"
        assert "stopped" in response.json()["message"]


@pytest.mark.asyncio
async def test_stop_execution_not_found(client, mock_auth, mock_team_orchestrator):
    """Testa a parada de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar False (execução não encontrada ou não pode ser parada)
    mock_team_orchestrator.stop_execution.return_value = False
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.post(f"/api/v1/executions/{execution_id}/stop")
        
        # Assert
        assert response.status_code == 404
        mock_team_orchestrator.stop_execution.assert_called_once()
        assert f"Execution {execution_id} not found or not running" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_executions(client, mock_auth, mock_team_orchestrator):
    """Testa a listagem de execuções."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar uma lista de execuções
    execution_response = TeamExecutionResponse(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.COMPLETED,
        created_at="2023-01-01T00:00:00Z",
        started_at="2023-01-01T00:00:00Z",
        completed_at="2023-01-01T00:05:00Z"
    )
    mock_team_orchestrator.list_executions.return_value = [execution_response]
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get("/api/v1/executions")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.list_executions.assert_called_once_with(
            user_id,
            None,  # team_id
            10,    # limit
            0      # offset
        )
        assert len(response.json()) == 1
        assert response.json()[0]["execution_id"] == str(execution_id)


@pytest.mark.asyncio
async def test_list_executions_with_team_filter(client, mock_auth, mock_team_orchestrator):
    """Testa a listagem de execuções filtradas por equipe."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar uma lista de execuções
    execution_response = TeamExecutionResponse(
        execution_id=execution_id,
        team_id=team_id,
        status=ExecutionStatus.COMPLETED,
        created_at="2023-01-01T00:00:00Z",
        started_at="2023-01-01T00:00:00Z",
        completed_at="2023-01-01T00:05:00Z"
    )
    mock_team_orchestrator.list_executions.return_value = [execution_response]
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.get(f"/api/v1/executions?team_id={team_id}")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.list_executions.assert_called_once_with(
            user_id,
            team_id,  # team_id
            10,       # limit
            0         # offset
        )
        assert len(response.json()) == 1
        assert response.json()[0]["team_id"] == str(team_id)


@pytest.mark.asyncio
async def test_get_execution_logs(client, mock_auth, mock_team_execution_repository):
    """Testa a obtenção de logs de uma execução."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar a execução
    mock_team_execution_repository.get_execution.return_value = MagicMock()
    
    # Configura o mock para retornar logs de execução
    log_entries = [
        ExecutionLogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level="info",
            agent_id="agent-123",
            message="Agent execution started",
            details={
                "step_order": 1,
                "suna_agent_run_id": "00000000-0000-0000-0000-000000000004"
            }
        ),
        ExecutionLogEntry(
            timestamp="2023-01-01T00:01:00Z",
            level="info",
            agent_id="agent-123",
            message="Agent execution completed successfully",
            details={
                "step_order": 1,
                "execution_time": 60
            }
        )
    ]
    mock_team_execution_repository.get_execution_logs.return_value = log_entries
    
    with patch("app.core.dependencies.get_team_execution_repository", return_value=mock_team_execution_repository):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/logs")
        
        # Assert
        assert response.status_code == 200
        mock_team_execution_repository.get_execution.assert_called_once_with(execution_id, user_id)
        mock_team_execution_repository.get_execution_logs.assert_called_once_with(
            execution_id,
            100,  # limit
            0,    # offset
            None, # log_types
            None  # agent_id
        )
        assert len(response.json()) == 2
        assert response.json()[0]["level"] == "info"
        assert response.json()[0]["agent_id"] == "agent-123"


@pytest.mark.asyncio
async def test_get_execution_logs_with_filters(client, mock_auth, mock_team_execution_repository):
    """Testa a obtenção de logs de uma execução com filtros."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    agent_id = "agent-123"
    
    # Configura o mock para retornar a execução
    mock_team_execution_repository.get_execution.return_value = MagicMock()
    
    # Configura o mock para retornar logs de execução
    log_entries = [
        ExecutionLogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level="info",
            agent_id=agent_id,
            message="Agent execution started",
            details={
                "step_order": 1,
                "suna_agent_run_id": "00000000-0000-0000-0000-000000000004"
            }
        )
    ]
    mock_team_execution_repository.get_execution_logs.return_value = log_entries
    
    with patch("app.core.dependencies.get_team_execution_repository", return_value=mock_team_execution_repository):
        # Act
        response = client.get(
            f"/api/v1/executions/{execution_id}/logs?agent_id={agent_id}&log_types=info,error"
        )
        
        # Assert
        assert response.status_code == 200
        mock_team_execution_repository.get_execution.assert_called_once_with(execution_id, user_id)
        mock_team_execution_repository.get_execution_logs.assert_called_once_with(
            execution_id,
            100,                # limit
            0,                  # offset
            ["info", "error"],  # log_types
            agent_id            # agent_id
        )
        assert len(response.json()) == 1
        assert response.json()[0]["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_get_execution_logs_execution_not_found(client, mock_auth, mock_team_execution_repository):
    """Testa a obtenção de logs de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar None (execução não encontrada)
    mock_team_execution_repository.get_execution.return_value = None
    
    with patch("app.core.dependencies.get_team_execution_repository", return_value=mock_team_execution_repository):
        # Act
        response = client.get(f"/api/v1/executions/{execution_id}/logs")
        
        # Assert
        assert response.status_code == 404
        mock_team_execution_repository.get_execution.assert_called_once()
        assert f"Execution {execution_id} not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_execution_success(client, mock_auth, mock_team_orchestrator):
    """Testa a exclusão bem-sucedida de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Do mock_auth
    
    # Configura o mock para retornar True (execução excluída com sucesso)
    mock_team_orchestrator.delete_execution.return_value = True
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.delete(f"/api/v1/executions/{execution_id}")
        
        # Assert
        assert response.status_code == 200
        mock_team_orchestrator.delete_execution.assert_called_once_with(execution_id, user_id)
        assert response.json()["status"] == "success"
        assert "deleted" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_execution_not_found(client, mock_auth, mock_team_orchestrator):
    """Testa a exclusão de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para retornar False (execução não encontrada)
    mock_team_orchestrator.delete_execution.return_value = False
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        response = client.delete(f"/api/v1/executions/{execution_id}")
        
        # Assert
        assert response.status_code == 404
        mock_team_orchestrator.delete_execution.assert_called_once()
        assert f"Execution {execution_id} not found" in response.json()["detail"]