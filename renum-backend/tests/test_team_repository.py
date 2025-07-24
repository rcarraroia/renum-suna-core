"""
Testes para o repositório de equipes.

Este módulo contém testes para o repositório de equipes.
"""

import pytest
from unittest.mock import MagicMock
import uuid
from datetime import datetime

from app.repositories.team_repository import TeamRepository
from app.models.team_models import TeamCreate, WorkflowDefinition, WorkflowType, AgentConfig, InputConfig, InputSource


@pytest.fixture
def team_repository(mock_db):
    """
    Fixture para o repositório de equipes.
    
    Args:
        mock_db: Mock do banco de dados
        
    Returns:
        Repositório de equipes
    """
    return TeamRepository()


@pytest.mark.asyncio
async def test_create_team(team_repository, mock_db):
    """
    Testa a criação de uma equipe.
    
    Args:
        team_repository: Repositório de equipes
        mock_db: Mock do banco de dados
    """
    # Configura o mock para retornar um resultado simulado
    mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{
            "team_id": "00000000-0000-0000-0000-000000000001",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "name": "Test Team",
            "description": "Test Description",
            "agent_ids": ["agent1", "agent2"],
            "workflow_definition": {
                "type": "sequential",
                "agents": [
                    {
                        "agent_id": "agent1",
                        "role": "member",
                        "execution_order": 1,
                        "input": {
                            "source": "initial_prompt"
                        }
                    },
                    {
                        "agent_id": "agent2",
                        "role": "member",
                        "execution_order": 2,
                        "input": {
                            "source": "agent_result",
                            "agent_id": "agent1"
                        }
                    }
                ]
            },
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }]
    )
    
    # Configura o mock para verificar se os agentes existem
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"agent_id": "agent1"}]
    )
    
    # Cria os dados da equipe
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    team_data = TeamCreate(
        name="Test Team",
        description="Test Description",
        agent_ids=["agent1", "agent2"],
        workflow_definition=WorkflowDefinition(
            type=WorkflowType.SEQUENTIAL,
            agents=[
                AgentConfig(
                    agent_id="agent1",
                    execution_order=1,
                    input=InputConfig(
                        source=InputSource.INITIAL_PROMPT
                    )
                ),
                AgentConfig(
                    agent_id="agent2",
                    execution_order=2,
                    input=InputConfig(
                        source=InputSource.AGENT_RESULT,
                        agent_id="agent1"
                    )
                )
            ]
        )
    )
    
    # Cria a equipe
    result = await team_repository.create_team(user_id, team_data)
    
    # Verifica o resultado
    assert result.name == "Test Team"
    assert result.description == "Test Description"
    assert result.agent_ids == ["agent1", "agent2"]
    assert result.workflow_definition.type == WorkflowType.SEQUENTIAL
    assert len(result.workflow_definition.agents) == 2
    
    # Verifica se o mock foi chamado corretamente
    mock_db.table.assert_called_with("renum_agent_teams")
    mock_db.table.return_value.insert.assert_called_once()