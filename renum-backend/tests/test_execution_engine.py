"""
Testes para o motor de execução.

Este módulo contém testes para o motor de execução,
verificando a criação e execução de planos de execução.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

from app.services.execution_engine import ExecutionEngine
from app.models.team_models import (
    RenumTeamConfig,
    WorkflowType,
    ExecutionStatus,
    WorkflowDefinition,
    AgentConfig,
    AgentRole,
    InputConfig,
    InputSource
)


@pytest.mark.asyncio
async def test_create_execution_plan_sequential():
    """Testa a criação de um plano de execução sequencial."""
    # Arrange
    execution_repository = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    engine = ExecutionEngine(
        execution_repository,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    team_config = RenumTeamConfig(
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="Test Team",
        agent_ids=["agent-1", "agent-2", "agent-3"],
        workflow_definition=WorkflowDefinition(
            type=WorkflowType.SEQUENTIAL,
            agents=[
                AgentConfig(
                    agent_id="agent-1",
                    role=AgentRole.LEADER,
                    execution_order=1,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                AgentConfig(
                    agent_id="agent-2",
                    role=AgentRole.MEMBER,
                    execution_order=2,
                    input=InputConfig(
                        source=InputSource.AGENT_RESULT,
                        agent_id="agent-1"
                    )
                ),
                AgentConfig(
                    agent_id="agent-3",
                    role=AgentRole.MEMBER,
                    execution_order=3,
                    input=InputConfig(
                        source=InputSource.AGENT_RESULT,
                        agent_id="agent-2"
                    )
                )
            ]
        )
    )
    
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Act
    plan = await engine.create_execution_plan(team_config, execution_id)
    
    # Assert
    assert plan.execution_id == execution_id
    assert plan.team_id == team_config.team_id
    assert plan.workflow_type == WorkflowType.SEQUENTIAL
    assert len(plan.steps) == 3
    
    # Verifica se os passos estão na ordem correta
    assert plan.steps[0].agent_id == "agent-1"
    assert plan.steps[1].agent_id == "agent-2"
    assert plan.steps[2].agent_id == "agent-3"
    
    # Verifica as dependências
    assert len(plan.steps[0].dependencies) == 0
    assert "agent-1" in plan.steps[1].dependencies
    assert "agent-2" in plan.steps[2].dependencies
    
    # Verifica se o plano foi salvo no banco de dados
    execution_repository.update_execution_plan.assert_called_once()


@pytest.mark.asyncio
async def test_create_execution_plan_parallel():
    """Testa a criação de um plano de execução paralelo."""
    # Arrange
    execution_repository = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    engine = ExecutionEngine(
        execution_repository,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    team_config = RenumTeamConfig(
        team_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="Test Team",
        agent_ids=["agent-1", "agent-2", "agent-3"],
        workflow_definition=WorkflowDefinition(
            type=WorkflowType.PARALLEL,
            agents=[
                AgentConfig(
                    agent_id="agent-1",
                    role=AgentRole.MEMBER,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                AgentConfig(
                    agent_id="agent-2",
                    role=AgentRole.MEMBER,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                AgentConfig(
                    agent_id="agent-3",
                    role=AgentRole.MEMBER,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                )
            ]
        )
    )
    
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Act
    plan = await engine.create_execution_plan(team_config, execution_id)
    
    # Assert
    assert plan.execution_id == execution_id
    assert plan.team_id == team_config.team_id
    assert plan.workflow_type == WorkflowType.PARALLEL
    assert len(plan.steps) == 3
    
    # Verifica se todos os passos têm dependências vazias
    for step in plan.steps:
        assert len(step.dependencies) == 0
    
    # Verifica se o plano foi salvo no banco de dados
    execution_repository.update_execution_plan.assert_called_once()


@pytest.mark.asyncio
async def test_execute_plan_success():
    """Testa a execução de um plano com sucesso."""
    # Arrange
    execution_repository = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    engine = ExecutionEngine(
        execution_repository,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para create_execution_plan
    engine.create_execution_plan = AsyncMock()
    
    # Mock para _execute_sequential_plan
    engine._execute_sequential_plan = AsyncMock(return_value=True)
    
    team_config = MagicMock()
    team_config.workflow_definition.type = WorkflowType.SEQUENTIAL
    
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    initial_prompt = "Test prompt"
    
    # Act
    result = await engine.execute_plan(execution_id, team_config, initial_prompt)
    
    # Assert
    assert result is True
    execution_repository.update_execution_status.assert_called_with(
        execution_id, ExecutionStatus.RUNNING
    )
    engine.create_execution_plan.assert_called_once()
    context_manager.create_context.assert_called_once()
    engine._execute_sequential_plan.assert_called_once()
    execution_repository.update_execution_status.assert_called_with(
        execution_id, ExecutionStatus.COMPLETED
    )


@pytest.mark.asyncio
async def test_execute_plan_failure():
    """Testa a execução de um plano com falha."""
    # Arrange
    execution_repository = AsyncMock()
    suna_client = AsyncMock()
    context_manager = AsyncMock()
    message_bus = AsyncMock()
    api_key_manager = AsyncMock()
    
    engine = ExecutionEngine(
        execution_repository,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )
    
    # Mock para create_execution_plan
    engine.create_execution_plan = AsyncMock()
    
    # Mock para _execute_sequential_plan que lança uma exceção
    engine._execute_sequential_plan = AsyncMock(side_effect=Exception("Test error"))
    
    team_config = MagicMock()
    team_config.workflow_definition.type = WorkflowType.SEQUENTIAL
    
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    initial_prompt = "Test prompt"
    
    # Act
    result = await engine.execute_plan(execution_id, team_config, initial_prompt)
    
    # Assert
    assert result is False
    execution_repository.update_execution_status.assert_called_with(
        execution_id, ExecutionStatus.FAILED, error_message="Error executing plan: Test error"
    )