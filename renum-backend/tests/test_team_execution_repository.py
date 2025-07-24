"""
Testes para o repositório de execuções de equipes.

Este módulo contém testes para o repositório de execuções de equipes,
verificando a criação, atualização, consulta e exclusão de execuções.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from app.repositories.team_execution_repository import TeamExecutionRepository
from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    TeamExecutionStatus,
    TeamExecutionResult,
    TeamAgentExecutionResponse,
    ExecutionStatus,
    ExecutionLogEntry
)


@pytest.fixture
def mock_db():
    """
    Mock para o banco de dados.
    Returns:
        MagicMock: Mock para o banco de dados
    """
    mock = MagicMock()
    
    # Configura o mock para simular operações de banco de dados
    table_mock = MagicMock()
    mock.table.return_value = table_mock
    
    # Configura o mock para simular operações de tabela
    select_mock = MagicMock()
    insert_mock = MagicMock()
    update_mock = MagicMock()
    delete_mock = MagicMock()
    
    table_mock.select.return_value = select_mock
    table_mock.insert.return_value = insert_mock
    table_mock.update.return_value = update_mock
    table_mock.delete.return_value = delete_mock
    
    # Configura os mocks para simular operações de consulta
    eq_mock = MagicMock()
    order_mock = MagicMock()
    range_mock = MagicMock()
    execute_mock = AsyncMock()
    
    select_mock.eq.return_value = eq_mock
    eq_mock.eq.return_value = eq_mock
    eq_mock.order.return_value = order_mock
    order_mock.range.return_value = range_mock
    
    # Configura os mocks para simular operações de atualização
    update_mock.eq.return_value = eq_mock
    
    # Configura os mocks para simular operações de exclusão
    delete_mock.eq.return_value = eq_mock
    
    # Configura o mock para simular execução de consultas
    eq_mock.execute.return_value = execute_mock
    order_mock.execute.return_value = execute_mock
    range_mock.execute.return_value = execute_mock
    
    return mock


@pytest.fixture
def repository(mock_db):
    """
    Repositório de execuções de equipe para testes.
    Args:
        mock_db: Mock para o banco de dados
    Returns:
        TeamExecutionRepository: Repositório de execuções de equipe
    """
    return TeamExecutionRepository(mock_db)


@pytest.mark.asyncio
async def test_create_execution(repository, mock_db):
    """Testa a criação de uma execução."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    execution_data = TeamExecutionCreate(
        team_id=team_id,
        initial_prompt="Test prompt"
    )
    
    # Configura o mock para simular a inserção
    mock_db.table().insert().execute.return_value = MagicMock()
    
    # Act
    result = await repository.create_execution(user_id, execution_data)
    
    # Assert
    assert result is not None
    assert result.team_id == team_id
    assert result.status == ExecutionStatus.PENDING
    assert result.initial_prompt == "Test prompt"
    mock_db.table().insert.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution(repository, mock_db):
    """Testa a obtenção de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para simular a consulta
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(
        data=[{
            "execution_id": str(execution_id),
            "team_id": "00000000-0000-0000-0000-000000000002",
            "user_id": str(user_id),
            "status": ExecutionStatus.RUNNING.value,
            "initial_prompt": "Test prompt",
            "created_at": datetime.now().isoformat()
        }]
    )
    
    # Act
    result = await repository.get_execution(execution_id, user_id)
    
    # Assert
    assert result is not None
    assert result["execution_id"] == str(execution_id)
    assert result["status"] == ExecutionStatus.RUNNING.value
    mock_db.table().select.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution_not_found(repository, mock_db):
    """Testa a obtenção de uma execução inexistente."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para simular a consulta sem resultados
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(data=[])
    
    # Act
    result = await repository.get_execution(execution_id, user_id)
    
    # Assert
    assert result is None
    mock_db.table().select.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution_status(repository, mock_db):
    """Testa a obtenção do status de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Configura o mock para simular a consulta da execução
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(
        data=[{
            "execution_id": str(execution_id),
            "team_id": str(team_id),
            "user_id": str(user_id),
            "status": ExecutionStatus.RUNNING.value,
            "initial_prompt": "Test prompt",
            "started_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }]
    )
    
    # Configura o mock para simular a consulta de execuções de agentes
    with patch.object(repository, "list_agent_executions") as mock_list_agent_executions:
        mock_list_agent_executions.return_value = [
            TeamAgentExecutionResponse(
                execution_id=execution_id,
                agent_id="agent-123",
                step_order=1,
                status=ExecutionStatus.COMPLETED,
                input_data={},
                output_data={"result": "Agent 123 result"},
                started_at=datetime.now(),
                completed_at=datetime.now()
            ),
            TeamAgentExecutionResponse(
                execution_id=execution_id,
                agent_id="agent-456",
                step_order=2,
                status=ExecutionStatus.RUNNING,
                input_data={},
                output_data=None,
                started_at=datetime.now(),
                completed_at=None
            )
        ]
        
        # Act
        result = await repository.get_execution_status(execution_id, user_id)
        
        # Assert
        assert result is not None
        assert result.execution_id == execution_id
        assert result.team_id == str(team_id)
        assert result.status == ExecutionStatus.RUNNING
        assert result.progress == 50.0  # 1 de 2 agentes concluídos
        assert result.current_step == 2  # Agente em execução
        assert result.total_steps == 2  # Total de agentes
        mock_db.table().select.assert_called_once()
        mock_list_agent_executions.assert_called_once_with(execution_id)


@pytest.mark.asyncio
async def test_get_execution_result(repository, mock_db):
    """Testa a obtenção do resultado de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Configura o mock para simular a consulta da execução
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(
        data=[{
            "execution_id": str(execution_id),
            "team_id": str(team_id),
            "user_id": str(user_id),
            "status": ExecutionStatus.COMPLETED.value,
            "initial_prompt": "Test prompt",
            "final_result": {"summary": "Test result"},
            "cost_metrics": {"total_cost_usd": 0.15},
            "usage_metrics": {"total_tokens": 5000},
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }]
    )
    
    # Act
    result = await repository.get_execution_result(execution_id, user_id)
    
    # Assert
    assert result is not None
    assert result.execution_id == execution_id
    assert result.team_id == str(team_id)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.final_result == {"summary": "Test result"}
    assert result.cost_metrics.cost_usd == 0.15
    assert result.usage_metrics.total_tokens == 5000
    mock_db.table().select.assert_called_once()


@pytest.mark.asyncio
async def test_update_execution_status(repository, mock_db):
    """Testa a atualização do status de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    status = ExecutionStatus.RUNNING
    
    # Configura o mock para simular a atualização
    mock_db.table().update().eq().execute.return_value = MagicMock()
    
    # Act
    result = await repository.update_execution_status(execution_id, status)
    
    # Assert
    assert result is True
    mock_db.table().update.assert_called_once()


@pytest.mark.asyncio
async def test_update_execution_result(repository, mock_db):
    """Testa a atualização do resultado de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    final_result = {"summary": "Test result"}
    
    # Configura o mock para simular a atualização
    mock_db.table().update().eq().execute.return_value = MagicMock()
    
    # Act
    result = await repository.update_execution_result(execution_id, final_result)
    
    # Assert
    assert result is True
    mock_db.table().update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_execution(repository, mock_db):
    """Testa a exclusão de uma execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para simular a consulta da execução
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(
        data=[{
            "execution_id": str(execution_id),
            "user_id": str(user_id)
        }]
    )
    
    # Configura o mock para simular a exclusão
    mock_db.table().delete().eq().eq().execute.return_value = MagicMock()
    
    # Act
    result = await repository.delete_execution(execution_id, user_id)
    
    # Assert
    assert result is True
    mock_db.table().select.assert_called_once()
    mock_db.table().delete.assert_called_once()


@pytest.mark.asyncio
async def test_list_executions(repository, mock_db):
    """Testa a listagem de execuções."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    team_id = UUID("00000000-0000-0000-0000-000000000002")
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para simular a consulta
    mock_db.table().select().eq().eq().order().range().execute.return_value = MagicMock(
        data=[{
            "execution_id": str(execution_id),
            "team_id": str(team_id),
            "user_id": str(user_id),
            "status": ExecutionStatus.COMPLETED.value,
            "initial_prompt": "Test prompt",
            "final_result": {"summary": "Test result"},
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }]
    )
    
    # Act
    result = await repository.list_executions(user_id, team_id, 10, 0)
    
    # Assert
    assert len(result) == 1
    assert result[0].execution_id == execution_id
    assert result[0].team_id == str(team_id)
    assert result[0].status == ExecutionStatus.COMPLETED
    mock_db.table().select.assert_called_once()


@pytest.mark.asyncio
async def test_count_active_executions(repository, mock_db):
    """Testa a contagem de execuções ativas."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para simular a consulta
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(
        data=[{}, {}]  # 2 execuções ativas
    )
    
    # Act
    result = await repository.count_active_executions(user_id)
    
    # Assert
    assert result == 2
    mock_db.table().select.assert_called_once()


@pytest.mark.asyncio
async def test_get_execution_logs(repository, mock_db):
    """Testa a obtenção de logs de execução."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000003")
    
    # Configura o mock para simular a consulta de execuções de agentes
    with patch.object(repository, "list_agent_executions") as mock_list_agent_executions:
        mock_list_agent_executions.return_value = [
            TeamAgentExecutionResponse(
                execution_id=execution_id,
                agent_id="agent-123",
                step_order=1,
                status=ExecutionStatus.COMPLETED,
                input_data={},
                output_data={"result": "Agent 123 result"},
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        ]
        
        # Act
        result = await repository.get_execution_logs(execution_id)
        
        # Assert
        assert len(result) > 0
        assert isinstance(result[0], ExecutionLogEntry)
        assert result[0].agent_id == "agent-123"
        mock_list_agent_executions.assert_called_once_with(execution_id)