"""
Testes para os validadores.

Este módulo contém testes para as funções de validação do sistema.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID

from app.core.validators import (
    validate_agent_ownership,
    validate_team_limits,
    validate_team_update,
    validate_execution_limits
)
from app.models.team_models import TeamCreate, TeamUpdate, WorkflowDefinition


@pytest.mark.asyncio
async def test_validate_agent_ownership_success():
    """Testa a validação bem-sucedida da propriedade de agentes."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_ids = ["agent-123", "agent-456"]
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    suna_client.get_agent = AsyncMock()
    
    # Configura o mock para retornar agentes que pertencem ao usuário
    suna_client.get_agent.side_effect = lambda agent_id: {
        "agent_id": agent_id,
        "user_id": user_id
    }
    
    # Act
    result = await validate_agent_ownership(user_id, agent_ids, suna_client)
    
    # Assert
    assert result is True
    assert suna_client.get_agent.call_count == 2


@pytest.mark.asyncio
async def test_validate_agent_ownership_agent_not_found():
    """Testa a validação da propriedade de agentes quando um agente não é encontrado."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_ids = ["agent-123", "agent-nonexistent"]
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    suna_client.get_agent = AsyncMock()
    
    # Configura o mock para retornar None para o agente não encontrado
    suna_client.get_agent.side_effect = lambda agent_id: {
        "agent_id": agent_id,
        "user_id": user_id
    } if agent_id == "agent-123" else None
    
    # Act & Assert
    with pytest.raises(ValueError, match="Agent agent-nonexistent not found"):
        await validate_agent_ownership(user_id, agent_ids, suna_client)


@pytest.mark.asyncio
async def test_validate_agent_ownership_agent_not_owned():
    """Testa a validação da propriedade de agentes quando um agente não pertence ao usuário."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    other_user_id = UUID("00000000-0000-0000-0000-000000000002")
    agent_ids = ["agent-123", "agent-456"]
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    suna_client.get_agent = AsyncMock()
    
    # Configura o mock para retornar um agente que não pertence ao usuário
    suna_client.get_agent.side_effect = lambda agent_id: {
        "agent_id": agent_id,
        "user_id": user_id if agent_id == "agent-123" else other_user_id
    }
    
    # Act & Assert
    with pytest.raises(ValueError, match="Agent agent-456 does not belong to the user"):
        await validate_agent_ownership(user_id, agent_ids, suna_client)


@pytest.mark.asyncio
async def test_validate_team_limits_success():
    """Testa a validação bem-sucedida dos limites de uma equipe."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Cria uma equipe com 3 agentes (abaixo do limite)
    team_data = TeamCreate(
        name="Test Team",
        description="Test Description",
        agent_ids=["agent-123", "agent-456", "agent-789"],
        workflow_definition=MagicMock()
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    team_repository.list_teams = AsyncMock()
    
    # Configura o mock para retornar 5 equipes (abaixo do limite)
    team_repository.list_teams.return_value = MagicMock(total=5)
    
    # Act
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_AGENTS_PER_TEAM=10)):
        result = await validate_team_limits(team_data, user_id, team_repository)
    
    # Assert
    assert result is True
    team_repository.list_teams.assert_called_once_with(user_id, page=1, limit=1000)


@pytest.mark.asyncio
async def test_validate_team_limits_too_many_agents():
    """Testa a validação dos limites de uma equipe com muitos agentes."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Cria uma equipe com 11 agentes (acima do limite de 10)
    team_data = TeamCreate(
        name="Test Team",
        description="Test Description",
        agent_ids=[f"agent-{i}" for i in range(11)],
        workflow_definition=MagicMock()
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    
    # Act & Assert
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_AGENTS_PER_TEAM=10)):
        with pytest.raises(ValueError, match="Maximum number of agents per team is 10"):
            await validate_team_limits(team_data, user_id, team_repository)


@pytest.mark.asyncio
async def test_validate_team_limits_too_many_teams():
    """Testa a validação dos limites quando o usuário tem muitas equipes."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Cria uma equipe com 3 agentes (abaixo do limite)
    team_data = TeamCreate(
        name="Test Team",
        description="Test Description",
        agent_ids=["agent-123", "agent-456", "agent-789"],
        workflow_definition=MagicMock()
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    team_repository.list_teams = AsyncMock()
    
    # Configura o mock para retornar 100 equipes (no limite)
    team_repository.list_teams.return_value = MagicMock(total=100)
    
    # Act & Assert
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_AGENTS_PER_TEAM=10)):
        with pytest.raises(ValueError, match="Maximum number of teams per user reached"):
            await validate_team_limits(team_data, user_id, team_repository)


@pytest.mark.asyncio
async def test_validate_team_update_success():
    """Testa a validação bem-sucedida da atualização de uma equipe."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Dados de atualização da equipe
    team_data = TeamUpdate(
        name="Updated Team",
        description="Updated Description",
        agent_ids=["agent-123", "agent-456"]
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    team_repository.get_team = AsyncMock()
    
    # Configura o mock para retornar uma equipe existente
    team_repository.get_team.return_value = MagicMock(
        team_id=team_id,
        user_id=user_id
    )
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    suna_client.get_agent = AsyncMock()
    
    # Configura o mock para retornar agentes que pertencem ao usuário
    suna_client.get_agent.side_effect = lambda agent_id: {
        "agent_id": agent_id,
        "user_id": user_id
    }
    
    # Act
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_AGENTS_PER_TEAM=10)):
        result = await validate_team_update(team_data, team_id, user_id, team_repository, suna_client)
    
    # Assert
    assert result is True
    team_repository.get_team.assert_called_once_with(team_id, user_id)
    assert suna_client.get_agent.call_count == 2


@pytest.mark.asyncio
async def test_validate_team_update_team_not_found():
    """Testa a validação da atualização de uma equipe inexistente."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Dados de atualização da equipe
    team_data = TeamUpdate(
        name="Updated Team"
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    team_repository.get_team = AsyncMock()
    
    # Configura o mock para retornar None (equipe não encontrada)
    team_repository.get_team.return_value = None
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    
    # Act & Assert
    with pytest.raises(ValueError, match=f"Team {team_id} not found"):
        await validate_team_update(team_data, team_id, user_id, team_repository, suna_client)


@pytest.mark.asyncio
async def test_validate_team_update_too_many_agents():
    """Testa a validação da atualização de uma equipe com muitos agentes."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Dados de atualização da equipe com 11 agentes (acima do limite de 10)
    team_data = TeamUpdate(
        name="Updated Team",
        agent_ids=[f"agent-{i}" for i in range(11)]
    )
    
    # Mock do repositório de equipes
    team_repository = MagicMock()
    team_repository.get_team = AsyncMock()
    
    # Configura o mock para retornar uma equipe existente
    team_repository.get_team.return_value = MagicMock(
        team_id=team_id,
        user_id=user_id
    )
    
    # Mock do cliente Suna
    suna_client = MagicMock()
    
    # Act & Assert
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_AGENTS_PER_TEAM=10)):
        with pytest.raises(ValueError, match="Maximum number of agents per team is 10"):
            await validate_team_update(team_data, team_id, user_id, team_repository, suna_client)


@pytest.mark.asyncio
async def test_validate_execution_limits_success():
    """Testa a validação bem-sucedida dos limites de execução."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Mock do repositório de execuções
    execution_repository = MagicMock()
    execution_repository.count_active_executions = AsyncMock()
    
    # Configura o mock para retornar 2 execuções ativas (abaixo do limite)
    execution_repository.count_active_executions.return_value = 2
    
    # Act
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_CONCURRENT_EXECUTIONS=5)):
        result = await validate_execution_limits(user_id, execution_repository)
    
    # Assert
    assert result is True
    execution_repository.count_active_executions.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_execution_limits_too_many_executions():
    """Testa a validação dos limites de execução quando há muitas execuções ativas."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Mock do repositório de execuções
    execution_repository = MagicMock()
    execution_repository.count_active_executions = AsyncMock()
    
    # Configura o mock para retornar 5 execuções ativas (no limite)
    execution_repository.count_active_executions.return_value = 5
    
    # Act & Assert
    with patch("app.core.validators.get_settings", return_value=MagicMock(MAX_CONCURRENT_EXECUTIONS=5)):
        with pytest.raises(ValueError, match="Maximum number of concurrent executions reached"):
            await validate_execution_limits(user_id, execution_repository)