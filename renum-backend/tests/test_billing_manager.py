"""
Testes para o gerenciador de billing.

Este módulo contém testes para o gerenciador de billing,
verificando a verificação de limites de uso, cálculo de custos e registro de métricas.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.services.billing_manager import BillingManager
from app.models.team_models import UsageMetrics


@pytest.fixture
def mock_execution_repository():
    """
    Mock para o repositório de execuções.
    Returns:
        AsyncMock: Mock para o repositório de execuções
    """
    mock = AsyncMock()
    mock.count_active_executions = AsyncMock(return_value=0)
    mock.list_executions_by_date = AsyncMock(return_value=[])
    mock.update_agent_execution = AsyncMock(return_value=True)
    mock.update_execution_result = AsyncMock(return_value=True)
    mock.register_usage = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def billing_manager(mock_execution_repository):
    """
    Gerenciador de billing para testes.
    Args:
        mock_execution_repository: Mock para o repositório de execuções
    Returns:
        BillingManager: Gerenciador de billing
    """
    return BillingManager(mock_execution_repository)


@pytest.mark.asyncio
async def test_check_usage_limits_success(billing_manager, mock_execution_repository):
    """Testa a verificação bem-sucedida de limites de uso."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_execution_repository.count_active_executions.return_value = 3  # Abaixo do limite
    
    # Mock para get_monthly_usage
    billing_manager.get_monthly_usage = AsyncMock(return_value={"total_cost_usd": 50.0})  # Abaixo do limite
    
    # Act
    result = await billing_manager.check_usage_limits(user_id)
    
    # Assert
    assert result is True
    mock_execution_repository.count_active_executions.assert_called_once_with(user_id)
    billing_manager.get_monthly_usage.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_check_usage_limits_exceeds_concurrent_executions(billing_manager, mock_execution_repository):
    """Testa a verificação de limites de uso quando o limite de execuções concorrentes é excedido."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_execution_repository.count_active_executions.return_value = 5  # No limite
    
    # Act & Assert
    with pytest.raises(ValueError, match="Maximum number of concurrent executions reached"):
        await billing_manager.check_usage_limits(user_id)
    
    mock_execution_repository.count_active_executions.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_check_usage_limits_exceeds_monthly_usage(billing_manager, mock_execution_repository):
    """Testa a verificação de limites de uso quando o limite de uso mensal é excedido."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_execution_repository.count_active_executions.return_value = 3  # Abaixo do limite
    
    # Mock para get_monthly_usage
    billing_manager.get_monthly_usage = AsyncMock(return_value={"total_cost_usd": 100.0})  # No limite
    
    # Act & Assert
    with pytest.raises(ValueError, match="Monthly usage limit reached"):
        await billing_manager.check_usage_limits(user_id)
    
    mock_execution_repository.count_active_executions.assert_called_once_with(user_id)
    billing_manager.get_monthly_usage.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_monthly_usage(billing_manager, mock_execution_repository):
    """Testa a obtenção do uso mensal."""
    # Arrange
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    # Configura o mock para retornar execuções com métricas
    mock_execution_repository.list_executions_by_date.return_value = [
        {
            "usage_metrics": {
                "tokens_input": 1000,
                "tokens_output": 500
            },
            "cost_metrics": {
                "cost_usd": 0.05
            }
        },
        {
            "usage_metrics": {
                "tokens_input": 2000,
                "tokens_output": 1000
            },
            "cost_metrics": {
                "cost_usd": 0.10
            }
        }
    ]
    
    # Act
    result = await billing_manager.get_monthly_usage(user_id)
    
    # Assert
    assert result["total_tokens_input"] == 3000
    assert result["total_tokens_output"] == 1500
    assert result["total_tokens"] == 4500
    assert result["total_cost_usd"] == 0.15
    mock_execution_repository.list_executions_by_date.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_agent_cost_gpt4(billing_manager):
    """Testa o cálculo de custo para o modelo GPT-4."""
    # Arrange
    usage_metrics = UsageMetrics(
        model_provider="openai",
        model_name="gpt-4",
        api_key_type="renum_native",
        tokens_input=1000,
        tokens_output=500,
        request_count=1
    )
    
    # Act
    cost = await billing_manager.calculate_agent_cost(usage_metrics)
    
    # Assert
    assert cost == 0.03 + 0.03  # $0.03 por 1K tokens de entrada + $0.03 por 0.5K tokens de saída


@pytest.mark.asyncio
async def test_calculate_agent_cost_gpt4o(billing_manager):
    """Testa o cálculo de custo para o modelo GPT-4o."""
    # Arrange
    usage_metrics = UsageMetrics(
        model_provider="openai",
        model_name="gpt-4o",
        api_key_type="renum_native",
        tokens_input=1000,
        tokens_output=500,
        request_count=1
    )
    
    # Act
    cost = await billing_manager.calculate_agent_cost(usage_metrics)
    
    # Assert
    assert cost == 0.005 + 0.0075  # $0.005 por 1K tokens de entrada + $0.0075 por 0.5K tokens de saída


@pytest.mark.asyncio
async def test_calculate_agent_cost_gpt35(billing_manager):
    """Testa o cálculo de custo para o modelo GPT-3.5."""
    # Arrange
    usage_metrics = UsageMetrics(
        model_provider="openai",
        model_name="gpt-3.5-turbo",
        api_key_type="renum_native",
        tokens_input=1000,
        tokens_output=500,
        request_count=1
    )
    
    # Act
    cost = await billing_manager.calculate_agent_cost(usage_metrics)
    
    # Assert
    assert cost == 0.001 + 0.001  # $0.001 por 1K tokens de entrada + $0.001 por 0.5K tokens de saída


@pytest.mark.asyncio
async def test_calculate_agent_cost_claude(billing_manager):
    """Testa o cálculo de custo para o modelo Claude."""
    # Arrange
    usage_metrics = UsageMetrics(
        model_provider="anthropic",
        model_name="claude-3-sonnet",
        api_key_type="renum_native",
        tokens_input=1000,
        tokens_output=500,
        request_count=1
    )
    
    # Act
    cost = await billing_manager.calculate_agent_cost(usage_metrics)
    
    # Assert
    assert cost == 0.003 + 0.0075  # $0.003 por 1K tokens de entrada + $0.0075 por 0.5K tokens de saída


@pytest.mark.asyncio
async def test_register_usage(billing_manager, mock_execution_repository):
    """Testa o registro de uso."""
    # Arrange
    execution_id = UUID("00000000-0000-0000-0000-000000000001")
    agent_id = "agent-123"
    usage_metrics = UsageMetrics(
        model_provider="openai",
        model_name="gpt-4",
        api_key_type="renum_native",
        tokens_input=1000,
        tokens_output=500,
        request_count=1
    )
    
    # Mock para calculate_agent_cost
    billing_manager.calculate_agent_cost = AsyncMock(return_value=0.06)
    
    # Act
    result = await billing_manager.register_usage(execution_id, agent_id, usage_metrics)
    
    # Assert
    assert result is True
    billing_manager.calculate_agent_cost.assert_called_once_with(usage_metrics)
    mock_execution_repository.update_agent_execution.assert_called_once()
    mock_execution_repository.register_usage.assert_called_once()