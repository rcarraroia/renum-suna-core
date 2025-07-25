"""
Testes para o serviço de tratamento de erros de execução
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.execution_error_handler import (
    ExecutionErrorHandler,
    ExecutionError,
    ExecutionErrorType,
    ExecutionErrorSeverity
)
from app.models.team_models import TeamExecution, ExecutionStatus
from app.services.websocket_manager import WebSocketManager
from app.services.notification_service import NotificationService

@pytest.fixture
def mock_websocket_manager():
    """Mock do gerenciador WebSocket"""
    mock = Mock(spec=WebSocketManager)
    mock.broadcast_to_channel = AsyncMock()
    mock.send_to_user = AsyncMock()
    return mock

@pytest.fixture
def mock_notification_service():
    """Mock do serviço de notificações"""
    mock = Mock(spec=NotificationService)
    mock.create_notification = AsyncMock()
    return mock

@pytest.fixture
def error_handler(mock_websocket_manager, mock_notification_service):
    """Instância do manipulador de erros"""
    return ExecutionErrorHandler(
        websocket_manager=mock_websocket_manager,
        notification_service=mock_notification_service
    )

@pytest.fixture
def sample_execution():
    """Execução de exemplo"""
    return TeamExecution(
        id="exec123",
        team_id="team456",
        created_by="user789",
        status=ExecutionStatus.RUNNING,
        created_at=datetime.utcnow()
    )

class TestExecutionError:
    """Testes para a classe ExecutionError"""
    
    def test_execution_error_creation(self):
        """Testa a criação de um erro de execução"""
        error = ExecutionError(
            error_type=ExecutionErrorType.AGENT_TIMEOUT,
            message="Agent timed out after 30 seconds",
            severity=ExecutionErrorSeverity.MEDIUM,
            agent_id="agent123",
            step_name="data_processing"
        )
        
        assert error.error_type == ExecutionErrorType.AGENT_TIMEOUT
        assert error.message == "Agent timed out after 30 seconds"
        assert error.severity == ExecutionErrorSeverity.MEDIUM
        assert error.agent_id == "agent123"
        assert error.step_name == "data_processing"
        assert error.recoverable is True
        assert error.retry_count == 0
        assert error.max_retries == 3

    def test_execution_error_can_retry(self):
        """Testa se o erro pode ser reprocessado"""
        # Erro recuperável com tentativas restantes
        error = ExecutionError(
            error_type=ExecutionErrorType.NETWORK_ERROR,
            message="Connection failed",
            retry_count=1,
            max_retries=3
        )
        assert error.can_retry() is True
        
        # Erro recuperável sem tentativas restantes
        error.retry_count = 3
        assert error.can_retry() is False
        
        # Erro não recuperável
        error.recoverable = False
        error.retry_count = 0
        assert error.can_retry() is False

    def test_execution_error_to_dict(self):
        """Testa a conversão do erro para dicionário"""
        timestamp = datetime.utcnow()
        error = ExecutionError(
            error_type=ExecutionErrorType.AGENT_CRASH,
            message="Segmentation fault",
            severity=ExecutionErrorSeverity.HIGH,
            details={"exit_code": -11},
            timestamp=timestamp
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "agent_crash"
        assert error_dict["message"] == "Segmentation fault"
        assert error_dict["severity"] == "high"
        assert error_dict["details"] == {"exit_code": -11}
        assert error_dict["timestamp"] == timestamp.isoformat()

class TestExecutionErrorHandler:
    """Testes para o manipulador de erros de execução"""
    
    def test_classify_error_by_message(self, error_handler):
        """Testa a classificação de erro por mensagem"""
        # Timeout
        error_type = error_handler.classify_error("Connection timeout after 30 seconds")
        assert error_type == ExecutionErrorType.AGENT_TIMEOUT
        
        # Network error
        error_type = error_handler.classify_error("Connection refused by server")
        assert error_type == ExecutionErrorType.NETWORK_ERROR
        
        # Authentication error
        error_type = error_handler.classify_error("Authentication failed: invalid token")
        assert error_type == ExecutionErrorType.AUTHENTICATION_ERROR
        
        # Resource exhausted
        error_type = error_handler.classify_error("Out of memory error")
        assert error_type == ExecutionErrorType.RESOURCE_EXHAUSTED
        
        # Unknown error
        error_type = error_handler.classify_error("Unknown error occurred")
        assert error_type == ExecutionErrorType.SYSTEM_ERROR

    def test_classify_error_by_exception(self, error_handler):
        """Testa a classificação de erro por exceção"""
        # TimeoutError
        error_type = error_handler.classify_error("Error", TimeoutError())
        assert error_type == ExecutionErrorType.AGENT_TIMEOUT
        
        # ConnectionError
        error_type = error_handler.classify_error("Error", ConnectionError())
        assert error_type == ExecutionErrorType.NETWORK_ERROR
        
        # MemoryError
        error_type = error_handler.classify_error("Error", MemoryError())
        assert error_type == ExecutionErrorType.RESOURCE_EXHAUSTED
        
        # ValueError
        error_type = error_handler.classify_error("Error", ValueError())
        assert error_type == ExecutionErrorType.INVALID_INPUT

    def test_determine_severity(self, error_handler, sample_execution):
        """Testa a determinação da severidade do erro"""
        # Crítico
        severity = error_handler.determine_severity(
            ExecutionErrorType.AUTHENTICATION_ERROR, 
            sample_execution
        )
        assert severity == ExecutionErrorSeverity.CRITICAL
        
        # Alto
        severity = error_handler.determine_severity(
            ExecutionErrorType.AGENT_CRASH, 
            sample_execution
        )
        assert severity == ExecutionErrorSeverity.HIGH
        
        # Médio
        severity = error_handler.determine_severity(
            ExecutionErrorType.NETWORK_ERROR, 
            sample_execution
        )
        assert severity == ExecutionErrorSeverity.MEDIUM
        
        # Baixo
        severity = error_handler.determine_severity(
            ExecutionErrorType.USER_CANCELLED, 
            sample_execution
        )
        assert severity == ExecutionErrorSeverity.LOW

    @pytest.mark.asyncio
    async def test_handle_execution_error_recoverable(
        self, 
        error_handler, 
        sample_execution, 
        mock_websocket_manager, 
        mock_notification_service
    ):
        """Testa o tratamento de erro recuperável"""
        with patch.object(error_handler, '_schedule_retry') as mock_schedule_retry:
            error = await error_handler.handle_execution_error(
                execution=sample_execution,
                error_message="Connection timeout",
                agent_id="agent123",
                step_name="data_fetch"
            )
            
            assert error.error_type == ExecutionErrorType.AGENT_TIMEOUT
            assert error.recoverable is True
            assert error.can_retry() is True
            
            # Verificar se foi agendado retry
            mock_schedule_retry.assert_called_once()
            
            # Verificar notificação WebSocket
            mock_websocket_manager.broadcast_to_channel.assert_called()
            
            # Verificar criação de notificação
            mock_notification_service.create_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_execution_error_non_recoverable(
        self, 
        error_handler, 
        sample_execution, 
        mock_websocket_manager, 
        mock_notification_service
    ):
        """Testa o tratamento de erro não recuperável"""
        with patch.object(error_handler, '_mark_execution_failed') as mock_mark_failed:
            error = await error_handler.handle_execution_error(
                execution=sample_execution,
                error_message="Invalid authentication token",
                agent_id="agent123"
            )
            
            assert error.error_type == ExecutionErrorType.AUTHENTICATION_ERROR
            assert error.recoverable is False
            assert error.can_retry() is False
            
            # Verificar se foi marcado como falhado
            mock_mark_failed.assert_called_once()
            
            # Verificar notificação WebSocket
            mock_websocket_manager.broadcast_to_channel.assert_called()

    @pytest.mark.asyncio
    async def test_notify_error_via_websocket(
        self, 
        error_handler, 
        sample_execution, 
        mock_websocket_manager
    ):
        """Testa a notificação de erro via WebSocket"""
        error = ExecutionError(
            error_type=ExecutionErrorType.NETWORK_ERROR,
            message="Connection failed"
        )
        
        await error_handler._notify_error_via_websocket(sample_execution, error)
        
        # Verificar chamadas para diferentes canais
        assert mock_websocket_manager.broadcast_to_channel.call_count == 2
        assert mock_websocket_manager.send_to_user.call_count == 1
        
        # Verificar canais corretos
        calls = mock_websocket_manager.broadcast_to_channel.call_args_list
        channels = [call[0][0] for call in calls]
        assert f"execution_{sample_execution.id}" in channels
        assert f"team_{sample_execution.team_id}" in channels

    @pytest.mark.asyncio
    async def test_create_error_notification(
        self, 
        error_handler, 
        sample_execution, 
        mock_notification_service
    ):
        """Testa a criação de notificação de erro"""
        error = ExecutionError(
            error_type=ExecutionErrorType.AGENT_CRASH,
            message="Agent crashed unexpectedly",
            severity=ExecutionErrorSeverity.HIGH
        )
        
        await error_handler._create_error_notification(sample_execution, error)
        
        mock_notification_service.create_notification.assert_called_once()
        call_args = mock_notification_service.create_notification.call_args
        
        assert call_args[1]["user_id"] == sample_execution.created_by
        assert "Agent Crash" in call_args[1]["title"]
        assert error.message in call_args[1]["message"]

    @pytest.mark.asyncio
    async def test_schedule_retry(self, error_handler, sample_execution):
        """Testa o agendamento de retry"""
        error = ExecutionError(
            error_type=ExecutionErrorType.NETWORK_ERROR,
            message="Connection failed",
            retry_count=1
        )
        
        await error_handler._schedule_retry(sample_execution, error)
        
        # Verificar se o status foi atualizado
        assert sample_execution.status == ExecutionStatus.PENDING
        assert sample_execution.retry_count == 2

    @pytest.mark.asyncio
    async def test_mark_execution_failed(
        self, 
        error_handler, 
        sample_execution, 
        mock_websocket_manager
    ):
        """Testa marcar execução como falhada"""
        error = ExecutionError(
            error_type=ExecutionErrorType.AUTHENTICATION_ERROR,
            message="Invalid credentials"
        )
        
        await error_handler._mark_execution_failed(sample_execution, error)
        
        # Verificar se o status foi atualizado
        assert sample_execution.status == ExecutionStatus.FAILED
        assert sample_execution.error_message == error.message
        assert sample_execution.completed_at is not None
        
        # Verificar notificação WebSocket
        mock_websocket_manager.broadcast_to_channel.assert_called()

    def test_get_error_recovery_suggestions(self, error_handler):
        """Testa as sugestões de recuperação"""
        error = ExecutionError(
            error_type=ExecutionErrorType.NETWORK_ERROR,
            message="Connection failed"
        )
        
        suggestions = error_handler.get_error_recovery_suggestions(error)
        
        assert len(suggestions) > 0
        assert any("conectividade" in suggestion.lower() for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_get_execution_error_history(self, error_handler):
        """Testa a obtenção do histórico de erros"""
        execution_id = "exec123"
        
        # Por enquanto retorna lista vazia (implementação mock)
        history = await error_handler.get_execution_error_history(execution_id)
        
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_error_statistics(self, error_handler):
        """Testa a obtenção de estatísticas de erros"""
        team_id = "team123"
        
        # Por enquanto retorna estatísticas mock
        stats = await error_handler.get_error_statistics(team_id)
        
        assert isinstance(stats, dict)
        assert "total_errors" in stats
        assert "errors_by_type" in stats
        assert "errors_by_severity" in stats

class TestErrorPatterns:
    """Testes para padrões de erro"""
    
    def test_timeout_patterns(self, error_handler):
        """Testa padrões de timeout"""
        messages = [
            "Request timeout after 30 seconds",
            "Connection timeout",
            "Operation timed out"
        ]
        
        for message in messages:
            error_type = error_handler.classify_error(message)
            assert error_type == ExecutionErrorType.AGENT_TIMEOUT

    def test_network_patterns(self, error_handler):
        """Testa padrões de erro de rede"""
        messages = [
            "Connection refused",
            "Network unreachable",
            "Host not found"
        ]
        
        for message in messages:
            error_type = error_handler.classify_error(message)
            assert error_type == ExecutionErrorType.NETWORK_ERROR

    def test_authentication_patterns(self, error_handler):
        """Testa padrões de erro de autenticação"""
        messages = [
            "Authentication failed",
            "Unauthorized access",
            "Invalid credentials"
        ]
        
        for message in messages:
            error_type = error_handler.classify_error(message)
            assert error_type == ExecutionErrorType.AUTHENTICATION_ERROR

class TestRetryStrategies:
    """Testes para estratégias de retry"""
    
    def test_retry_strategy_timeout(self, error_handler):
        """Testa estratégia de retry para timeout"""
        strategy = error_handler.retry_strategies[ExecutionErrorType.AGENT_TIMEOUT]
        
        assert strategy["max_retries"] == 3
        assert strategy["exponential_backoff"] is True
        assert len(strategy["delay_seconds"]) == 3

    def test_retry_strategy_authentication(self, error_handler):
        """Testa estratégia de retry para autenticação"""
        strategy = error_handler.retry_strategies[ExecutionErrorType.AUTHENTICATION_ERROR]
        
        assert strategy["max_retries"] == 0
        assert strategy["exponential_backoff"] is False
        assert len(strategy["delay_seconds"]) == 0

    def test_retry_strategy_network(self, error_handler):
        """Testa estratégia de retry para rede"""
        strategy = error_handler.retry_strategies[ExecutionErrorType.NETWORK_ERROR]
        
        assert strategy["max_retries"] == 5
        assert strategy["exponential_backoff"] is True
        assert len(strategy["delay_seconds"]) == 5