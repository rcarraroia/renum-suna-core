"""
Testes para a API de membros de equipes.

Este módulo contém testes para os endpoints da API de membros de equipes,
verificando a adição, atualização e remoção de membros.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from app.main import app
from app.models.team_models import (
    TeamResponse,
    WorkflowDefinition,
    WorkflowType,
    AgentRole,
    WorkflowAgent,
    InputSource
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
async def test_add_team_member(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a adição de um membro a uma equipe."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Cria uma cópia do mock_team_response para modificar
    updated_team = mock_team_response.copy(deep=True)
    updated_team.agent_ids.append("agent-new")
    
    # Configura o mock para retornar a equipe original e depois a equipe atualizada
    mock_team_repository.get_team.return_value = mock_team_response
    mock_team_repository.update_team.return_value = updated_team
    
    # Dados do novo membro
    new_member = {
        "agent_id": "agent-new",
        "role": "member",
        "execution_order": 4,
        "input": {
            "source": "initial_prompt"
        }
    }
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.post(
            f"/api/v1/teams/{team_id}/members",
            json=new_member
        )
        
        # Assert
        assert response.status_code == 201
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_called_once()
        assert "agent-new" in response.json()["agent_ids"]


@pytest.mark.asyncio
async def test_update_team_member(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a atualização de um membro de uma equipe."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    
    # Cria uma cópia do mock_team_response para modificar
    updated_team = mock_team_response.copy(deep=True)
    for agent in updated_team.workflow_definition.agents:
        if agent.agent_id == agent_id:
            agent.role = AgentRole.COORDINATOR
            agent.execution_order = 5
    
    # Configura o mock para retornar a equipe original e depois a equipe atualizada
    mock_team_repository.get_team.return_value = mock_team_response
    mock_team_repository.update_team.return_value = updated_team
    
    # Dados atualizados do membro
    updated_member = {
        "role": "coordinator",
        "execution_order": 5
    }
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.put(
            f"/api/v1/teams/{team_id}/members/{agent_id}",
            json=updated_member
        )
        
        # Assert
        assert response.status_code == 200
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_called_once()
        
        # Verifica se o agente foi atualizado corretamente
        found = False
        for agent in response.json()["workflow_definition"]["agents"]:
            if agent["agent_id"] == agent_id:
                assert agent["role"] == "coordinator"
                assert agent["execution_order"] == 5
                found = True
        
        assert found, "Agent not found in response"


@pytest.mark.asyncio
async def test_remove_team_member(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a remoção de um membro de uma equipe."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    
    # Cria uma cópia do mock_team_response para modificar
    # Garante que a equipe tenha pelo menos 2 agentes para poder remover um
    mock_team = mock_team_response.copy(deep=True)
    if len(mock_team.agent_ids) < 2:
        mock_team.agent_ids.append("agent-extra")
        mock_team.workflow_definition.agents.append(
            WorkflowAgent(
                agent_id="agent-extra",
                role=AgentRole.MEMBER,
                execution_order=99,
                input={"source": "initial_prompt"}
            )
        )
    
    # Cria a equipe atualizada sem o agente removido
    updated_team = mock_team.copy(deep=True)
    updated_team.agent_ids = [aid for aid in updated_team.agent_ids if aid != agent_id]
    updated_team.workflow_definition.agents = [
        agent for agent in updated_team.workflow_definition.agents if agent.agent_id != agent_id
    ]
    
    # Configura o mock para retornar a equipe original e depois a equipe atualizada
    mock_team_repository.get_team.return_value = mock_team
    mock_team_repository.update_team.return_value = updated_team
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.delete(
            f"/api/v1/teams/{team_id}/members/{agent_id}"
        )
        
        # Assert
        assert response.status_code == 200
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_called_once()
        
        # Verifica se o agente foi removido
        assert agent_id not in response.json()["agent_ids"]
        
        # Verifica se o agente foi removido do workflow_definition
        for agent in response.json()["workflow_definition"]["agents"]:
            assert agent["agent_id"] != agent_id


@pytest.mark.asyncio
async def test_remove_last_team_member_fails(client, mock_auth, mock_team_repository):
    """Testa que a remoção do último membro de uma equipe falha."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    
    # Cria uma equipe com apenas um agente
    team_with_one_agent = MagicMock()
    team_with_one_agent.agent_ids = [agent_id]
    team_with_one_agent.workflow_definition = MagicMock()
    team_with_one_agent.workflow_definition.agents = [
        MagicMock(agent_id=agent_id)
    ]
    
    # Configura o mock para retornar a equipe com um único agente
    mock_team_repository.get_team.return_value = team_with_one_agent
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.delete(
            f"/api/v1/teams/{team_id}/members/{agent_id}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "Cannot remove the last agent" in response.json()["detail"]
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_not_called()


@pytest.mark.asyncio
async def test_add_team_member_team_not_found(client, mock_auth, mock_team_repository):
    """Testa a adição de um membro a uma equipe inexistente."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para retornar None (equipe não encontrada)
    mock_team_repository.get_team.return_value = None
    
    # Dados do novo membro
    new_member = {
        "agent_id": "agent-new",
        "role": "member",
        "execution_order": 4,
        "input": {
            "source": "initial_prompt"
        }
    }
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.post(
            f"/api/v1/teams/{team_id}/members",
            json=new_member
        )
        
        # Assert
        assert response.status_code == 404
        assert f"Team {team_id} not found" in response.json()["detail"]
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_not_called()


@pytest.mark.asyncio
async def test_update_team_member_agent_not_found(client, mock_auth, mock_team_repository, mock_team_response):
    """Testa a atualização de um membro que não existe na equipe."""
    # Arrange
    team_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-nonexistent"
    
    # Configura o mock para retornar a equipe
    mock_team_repository.get_team.return_value = mock_team_response
    
    # Dados atualizados do membro
    updated_member = {
        "role": "coordinator",
        "execution_order": 5
    }
    
    with patch("app.core.dependencies.get_team_repository", return_value=mock_team_repository):
        # Act
        response = client.put(
            f"/api/v1/teams/{team_id}/members/{agent_id}",
            json=updated_member
        )
        
        # Assert
        assert response.status_code == 404
        assert f"Agent {agent_id} is not a member of this team" in response.json()["detail"]
        mock_team_repository.get_team.assert_called_once()
        mock_team_repository.update_team.assert_not_called()