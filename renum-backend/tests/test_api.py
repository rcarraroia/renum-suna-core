"""
Testes para a API.

Este módulo contém testes para os endpoints da API,
verificando a criação, consulta e execução de equipes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from app.main import app
from app.models.team_models import (
    TeamResponse,
    PaginatedTeamResponse,
    TeamExecutionResponse,
    TeamExecutionStatus,
    TeamExecutionResult,
    ExecutionStatus
)


@pytest.fixture
def client():
    """
    Cliente de teste para a API.
    
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


def test_health_check(client):
    """Testa o endpoint de verificação de saúde."""
    # Act
    response = client.get("/health")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root(client):
    """Testa o endpoint raiz."""
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 200
    assert "name" in response.json()
    assert "version" in response.json()
    assert "description" in response.json()
    assert "docs_url" in response.json()


@pytest.mark.asyncio
async def test_create_team(client, mock_auth, mock_team_repository, mock_team_create, mock_team_response):
    """Testa a criação de uma equipe."""
    # Arrange
    mock_team_repository.create_team.return_value = mock_team_response
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.post(
            "/api/v1/teams",
            json=mock_team_create.dict()
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["team_id"] == str(mock_team_response.team_id)
        assert response.json()["name"] == mock_team_response.name
        mock_team_repository.create_team.assert_called_once()


@pytest.mark.asyncio
async def test_list_teams(client, mock_auth, mock_team_repository):
    """Testa a listagem de equipes."""
    # Arrange
    mock_paginated_response = PaginatedTeamResponse(
        teams=[],
        total=0,
        page=1,
        limit=10,
        pages=0
    )
    mock_team_repository.list_teams.return_value = mock_paginated_response
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.get("/api/v1/teams")
        
        # Assert
        assert response.status_code == 200
        assert "teams" in response.json()
        assert "total" in response.json()
        assert "page" in response.json()
        assert "limit" in response.json()
        assert "pages" in response.json()
        mock_team_repository.list_teams.assert_called_once()


@pytest.mark.asyncio
async def test_get_team(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a obtenção de uma equipe."""
    # Arrange
    mock_team_repository.get_team.return_value = mock_team_response
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.get(f"/api/v1/teams/{mock_team_response.team_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["team_id"] == str(mock_team_response.team_id)
        assert response.json()["name"] == mock_team_response.name
        mock_team_repository.get_team.assert_called_once()


@pytest.mark.asyncio
async def test_update_team(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a atualização de uma equipe."""
    # Arrange
    mock_team_repository.update_team.return_value = mock_team_response
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.put(
            f"/api/v1/teams/{mock_team_response.team_id}",
            json={"name": "Updated Team"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["team_id"] == str(mock_team_response.team_id)
        assert response.json()["name"] == mock_team_response.name
        mock_team_repository.update_team.assert_called_once()


@pytest.mark.asyncio
async def test_delete_team(client, mock_auth, mock_team_repository):
    """Testa a exclusão de uma equipe."""
    # Arrange
    mock_team_repository.delete_team.return_value = True
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.delete(f"/api/v1/teams/{UUID('00000000-0000-0000-0000-000000000001')}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_team_repository.delete_team.assert_called_once()


@pytest.mark.asyncio
async def test_execute_team(client, mock_auth, mock_team_orchestrator):
    """Testa a execução de uma equipe."""
    # Arrange
    execution_response = TeamExecutionResponse(
        execution_id=UUID("00000000-0000-0000-0000-000000000003"),
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=ExecutionStatus.PENDING,
        created_at="2023-01-01T00:00:00Z"
    )
    mock_team_orchestrator.execute_team.return_value = execution_response
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        team_id = UUID("00000000-0000-0000-0000-000000000001")
        response = client.post(
            f"/api/v1/teams/{team_id}/execute",
            json={
                "team_id": str(team_id),
                "initial_prompt": "Test prompt"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["execution_id"] == str(execution_response.execution_id)
        assert response.json()["status"] == execution_response.status.value
        mock_team_orchestrator.execute_team.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution_status(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção do status de uma execução."""
    # Arrange
    execution_status = TeamExecutionStatus(
        execution_id=UUID("00000000-0000-0000-0000-000000000003"),
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=ExecutionStatus.RUNNING,
        progress=0.5,
        current_step=1,
        total_steps=2,
        active_agents=["agent-2"],
        completed_agents=["agent-1"],
        failed_agents=[],
        updated_at="2023-01-01T00:00:00Z"
    )
    mock_team_orchestrator.get_execution_status.return_value = execution_status
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        execution_id = UUID("00000000-0000-0000-0000-000000000003")
        response = client.get(f"/api/v1/executions/{execution_id}/status")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["execution_id"] == str(execution_status.execution_id)
        assert response.json()["status"] == execution_status.status.value
        assert response.json()["progress"] == execution_status.progress
        mock_team_orchestrator.get_execution_status.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution_result(client, mock_auth, mock_team_orchestrator):
    """Testa a obtenção do resultado de uma execução."""
    # Arrange
    execution_result = TeamExecutionResult(
        execution_id=UUID("00000000-0000-0000-0000-000000000003"),
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=ExecutionStatus.COMPLETED,
        final_result={"result": "Test result"},
        agent_results={
            "agent-1": {"result": "Agent 1 result"},
            "agent-2": {"result": "Agent 2 result"}
        },
        started_at="2023-01-01T00:00:00Z",
        completed_at="2023-01-01T00:01:00Z",
        execution_duration=60
    )
    mock_team_orchestrator.get_execution_result.return_value = execution_result
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        execution_id = UUID("00000000-0000-0000-0000-000000000003")
        response = client.get(f"/api/v1/executions/{execution_id}/result")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["execution_id"] == str(execution_result.execution_id)
        assert response.json()["status"] == execution_result.status.value
        assert response.json()["final_result"] == execution_result.final_result
        assert response.json()["agent_results"] == execution_result.agent_results
        mock_team_orchestrator.get_execution_result.assert_called_once()


@pytest.mark.asyncio
async def test_stop_execution(client, mock_auth, mock_team_orchestrator):
    """Testa a parada de uma execução."""
    # Arrange
    mock_team_orchestrator.stop_execution.return_value = True
    
    with patch("app.core.dependencies.get_team_orchestrator", return_value=mock_team_orchestrator):
        # Act
        execution_id = UUID("00000000-0000-0000-0000-000000000003")
        response = client.post(f"/api/v1/executions/{execution_id}/stop")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_team_orchestrator.stop_execution.assert_called_once()