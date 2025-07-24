"""
Testes para o orquestrador de equipes.

Este módulo contém testes para o orquestrador de equipes,
verificando a execução e monitoramento de equipes.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

from app.services.team_orchestrator import TeamOrchestrator
from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    ExecutionStatus
)


@pytest.mark.asyncio
async def test_execute_team_success():
    """Testa a execução de uma equipe com sucesso."""
    # Arrange
    team_repository = AsyncMock()
    execution_repository = AsyncMock()
    execution_engine = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    orchestrator = TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para _count_active_executions
    orchestrator._count_active_executions = AsyncMock(return_value=0)
    
    # Mock para team_repository.get_team_config
    team_config = MagicMock()
    team_repository.get_team_config.return_value = team_config
    
    # Mock para execution_repository.create_execution
    execution_response = TeamExecutionResponse(
        execution_id=UUID("00000000-0000-0000-0000-000000000003"),
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=ExecutionStatus.PENDING,
        created_at="2023-01-01T00:00:00Z"
    )
    execution_repository.create_execution.return_value = execution_response
    
    # Mock para asyncio.create_task
    with patch("asyncio.create_task") as mock_create_task:
        # Act
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        execution_data = TeamExecutionCreate(
            team_id=UUID("00000000-0000-0000-0000-000000000001"),
            initial_prompt="Test prompt"
        )
        
        result = await orchestrator.execute_team(user_id, execution_data)
        
        # Assert
        assert result == execution_response
        orchestrator._count_active_executions.assert_called_once_with(user_id)
        team_repository.get_team_config.assert_called_once_with(
            execution_data.team_id, user_id
        )
        execution_repository.create_execution.assert_called_once_with(
            user_id, execution_data
        )
        mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_execute_team_max_executions_reached():
    """Testa a execução de uma equipe quando o limite de execuções é atingido."""
    # Arrange
    team_repository = AsyncMock()
    execution_repository = AsyncMock()
    execution_engine = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    orchestrator = TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para _count_active_executions
    orchestrator._count_active_executions = AsyncMock(return_value=5)
    
    # Mock para settings
    orchestrator.settings = MagicMock()
    orchestrator.settings.MAX_CONCURRENT_EXECUTIONS = 5
    
    # Act & Assert
    user_id = UUID("00000000-0000-0000-0000-000000000002")
    execution_data = TeamExecutionCreate(
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        initial_prompt="Test prompt"
    )
    
    with pytest.raises(ValueError, match="Maximum number of concurrent executions"):
        await orchestrator.execute_team(user_id, execution_data)
    
    orchestrator._count_active_executions.assert_called_once_with(user_id)
    team_repository.get_team_config.assert_not_called()
    execution_repository.create_execution.assert_not_called()


@pytest.mark.asyncio
async def test_execute_team_background():
    """Testa a execução de uma equipe em background."""
    # Arrange
    team_repository = AsyncMock()
    execution_repository = AsyncMock()
    execution_engine = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    orchestrator = TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para _collect_metrics
    orchestrator._collect_metrics = AsyncMock()
    
    # Dados de teste
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_config = MagicMock()
    team_config.team_id = UUID("00000000-0000-0000-0000-000000000001")
    team_config.user_id = UUID("00000000-0000-0000-0000-000000000002")
    initial_prompt = "Test prompt"
    
    # Act
    await orchestrator._execute_team_background(execution_id, team_config, initial_prompt)
    
    # Assert
    assert str(execution_id) not in orchestrator.active_executions
    execution_engine.execute_plan.assert_called_once_with(
        execution_id, team_config, initial_prompt
    )
    orchestrator._collect_metrics.assert_called_once_with(execution_id)


@pytest.mark.asyncio
async def test_execute_team_background_error():
    """Testa a execução de uma equipe em background com erro."""
    # Arrange
    team_repository = AsyncMock()
    execution_repository = AsyncMock()
    execution_engine = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    orchestrator = TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para execution_engine.execute_plan que lança uma exceção
    execution_engine.execute_plan.side_effect = Exception("Test error")
    
    # Dados de teste
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    team_config = MagicMock()
    team_config.team_id = UUID("00000000-0000-0000-0000-000000000001")
    team_config.user_id = UUID("00000000-0000-0000-0000-000000000002")
    initial_prompt = "Test prompt"
    
    # Act
    await orchestrator._execute_team_background(execution_id, team_config, initial_prompt)
    
    # Assert
    assert str(execution_id) not in orchestrator.active_executions
    execution_engine.execute_plan.assert_called_once_with(
        execution_id, team_config, initial_prompt
    )
    execution_repository.update_execution_status.assert_called_with(
        execution_id, ExecutionStatus.FAILED, error_message="Error executing team: Test error"
    )


@pytest.mark.asyncio
async def test_stop_execution_success():
    """Testa a parada de uma execução com sucesso."""
    # Arrange
    team_repository = AsyncMock()
    execution_repository = AsyncMock()
    execution_engine = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    orchestrator = TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para execution_repository.get_execution
    execution_repository.get_execution.return_value = {
        "status": ExecutionStatus.RUNNING.value
    }
    
    # Mock para execution_repository.list_agent_executions
    agent_execution = MagicMock()
    agent_execution.status = ExecutionStatus.RUNNING
    agent_execution.suna_agent_run_id = UUID("00000000-0000-0000-0000-000000000004")
    execution_repository.list_agent_executions.return_value = [agent_execution]
    
    # Dados de teste
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Adiciona a execução à lista de ativas
    orchestrator.active_executions[str(execution_id)] = {
        "team_id": "00000000-0000-0000-0000-000000000001",
        "user_id": str(user_id),
        "started_at": "2023-01-01T00:00:00Z"
    }
    
    # Act
    result = await orchestrator.stop_execution(execution_id, user_id)
    
    # Assert
    assert result is True
    assert str(execution_id) not in orchestrator.active_executions
    execution_repository.get_execution.assert_called_once_with(execution_id, user_id)
    execution_repository.list_agent_executions.assert_called_once_with(execution_id)
    suna_client.stop_agent_run.assert_called_once_with(str(agent_execution.suna_agent_run_id))
    execution_repository.update_agent_execution.assert_called_once()
    execution_repository.update_execution_status.assert_called_with(
        execution_id, ExecutionStatus.CANCELLED, error_message="Execution cancelled by user"
    )