"""
Serviço para tratamento de erros específicos de execução
"""
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from app.models.team_models import TeamExecution, ExecutionStatus
from app.services.websocket_manager import WebSocketManager
from app.services.notification_service import NotificationService
from app.models.notification_models import NotificationType

logger = logging.getLogger(__name__)

class ExecutionErrorType(Enum):
    """Tipos de erro de execução"""
    AGENT_TIMEOUT = "agent_timeout"
    AGENT_CRASH = "agent_crash"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INVALID_INPUT = "invalid_input"
    DEPENDENCY_ERROR = "dependency_error"
    SYSTEM_ERROR = "system_error"
    USER_CANCELLED = "user_cancelled"
    QUOTA_EXCEEDED = "quota_exceeded"

class ExecutionErrorSeverity(Enum):
    """Severidade do erro"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ExecutionError:
    """Classe para representar um erro de execução"""
    
    def __init__(
        self,
        error_type: ExecutionErrorType,
        message: str,
        severity: ExecutionErrorSeverity = ExecutionErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3,
        agent_id: Optional[str] = None,
        step_name: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.agent_id = agent_id
        self.step_name = step_name
        self.timestamp = timestamp or datetime.utcnow()
        self.stack_trace = traceback.format_exc() if traceback.format_exc() != 'NoneType: None\n' else None

    def to_dict(self) -> Dict[str, Any]:
        """Converte o erro para dicionário"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "agent_id": self.agent_id,
            "step_name": self.step_name,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace
        }

    def can_retry(self) -> bool:
        """Verifica se o erro pode ser reprocessado"""
        return self.recoverable and self.retry_count < self.max_retries

class ExecutionErrorHandler:
    """Gerenciador de erros de execução"""
    
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        notification_service: NotificationService
    ):
        self.websocket_manager = websocket_manager
        self.notification_service = notification_service
        self.error_patterns = self._initialize_error_patterns()
        self.retry_strategies = self._initialize_retry_strategies()

    def _initialize_error_patterns(self) -> Dict[str, ExecutionErrorType]:
        """Inicializa padrões de erro para classificação automática"""
        return {
            "timeout": ExecutionErrorType.AGENT_TIMEOUT,
            "connection refused": ExecutionErrorType.NETWORK_ERROR,
            "authentication failed": ExecutionErrorType.AUTHENTICATION_ERROR,
            "unauthorized": ExecutionErrorType.AUTHENTICATION_ERROR,
            "memory": ExecutionErrorType.RESOURCE_EXHAUSTED,
            "disk space": ExecutionErrorType.RESOURCE_EXHAUSTED,
            "quota exceeded": ExecutionErrorType.QUOTA_EXCEEDED,
            "invalid input": ExecutionErrorType.INVALID_INPUT,
            "validation error": ExecutionErrorType.INVALID_INPUT,
            "dependency": ExecutionErrorType.DEPENDENCY_ERROR,
            "import error": ExecutionErrorType.DEPENDENCY_ERROR,
            "cancelled": ExecutionErrorType.USER_CANCELLED,
            "segmentation fault": ExecutionErrorType.AGENT_CRASH,
            "core dumped": ExecutionErrorType.AGENT_CRASH
        }

    def _initialize_retry_strategies(self) -> Dict[ExecutionErrorType, Dict[str, Any]]:
        """Inicializa estratégias de retry por tipo de erro"""
        return {
            ExecutionErrorType.AGENT_TIMEOUT: {
                "max_retries": 3,
                "delay_seconds": [30, 60, 120],
                "exponential_backoff": True
            },
            ExecutionErrorType.NETWORK_ERROR: {
                "max_retries": 5,
                "delay_seconds": [10, 20, 40, 80, 160],
                "exponential_backoff": True
            },
            ExecutionErrorType.RESOURCE_EXHAUSTED: {
                "max_retries": 2,
                "delay_seconds": [300, 600],
                "exponential_backoff": False
            },
            ExecutionErrorType.DEPENDENCY_ERROR: {
                "max_retries": 1,
                "delay_seconds": [60],
                "exponential_backoff": False
            },
            ExecutionErrorType.AGENT_CRASH: {
                "max_retries": 2,
                "delay_seconds": [120, 300],
                "exponential_backoff": False
            },
            ExecutionErrorType.AUTHENTICATION_ERROR: {
                "max_retries": 0,
                "delay_seconds": [],
                "exponential_backoff": False
            },
            ExecutionErrorType.INVALID_INPUT: {
                "max_retries": 0,
                "delay_seconds": [],
                "exponential_backoff": False
            },
            ExecutionErrorType.USER_CANCELLED: {
                "max_retries": 0,
                "delay_seconds": [],
                "exponential_backoff": False
            },
            ExecutionErrorType.QUOTA_EXCEEDED: {
                "max_retries": 0,
                "delay_seconds": [],
                "exponential_backoff": False
            }
        }

    def classify_error(self, error_message: str, exception: Optional[Exception] = None) -> ExecutionErrorType:
        """Classifica automaticamente o tipo de erro baseado na mensagem"""
        error_message_lower = error_message.lower()
        
        for pattern, error_type in self.error_patterns.items():
            if pattern in error_message_lower:
                return error_type
        
        # Classificação baseada no tipo de exceção
        if exception:
            if isinstance(exception, TimeoutError):
                return ExecutionErrorType.AGENT_TIMEOUT
            elif isinstance(exception, ConnectionError):
                return ExecutionErrorType.NETWORK_ERROR
            elif isinstance(exception, MemoryError):
                return ExecutionErrorType.RESOURCE_EXHAUSTED
            elif isinstance(exception, ValueError):
                return ExecutionErrorType.INVALID_INPUT
            elif isinstance(exception, ImportError):
                return ExecutionErrorType.DEPENDENCY_ERROR
        
        return ExecutionErrorType.SYSTEM_ERROR

    def determine_severity(self, error_type: ExecutionErrorType, execution: TeamExecution) -> ExecutionErrorSeverity:
        """Determina a severidade do erro"""
        # Erros críticos que impedem completamente a execução
        if error_type in [
            ExecutionErrorType.AUTHENTICATION_ERROR,
            ExecutionErrorType.QUOTA_EXCEEDED,
            ExecutionErrorType.INVALID_INPUT
        ]:
            return ExecutionErrorSeverity.CRITICAL
        
        # Erros de alta severidade
        if error_type in [
            ExecutionErrorType.AGENT_CRASH,
            ExecutionErrorType.RESOURCE_EXHAUSTED
        ]:
            return ExecutionErrorSeverity.HIGH
        
        # Erros de média severidade
        if error_type in [
            ExecutionErrorType.AGENT_TIMEOUT,
            ExecutionErrorType.NETWORK_ERROR,
            ExecutionErrorType.DEPENDENCY_ERROR
        ]:
            return ExecutionErrorSeverity.MEDIUM
        
        # Erros de baixa severidade
        return ExecutionErrorSeverity.LOW

    async def handle_execution_error(
        self,
        execution: TeamExecution,
        error_message: str,
        exception: Optional[Exception] = None,
        agent_id: Optional[str] = None,
        step_name: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> ExecutionError:
        """Trata um erro de execução"""
        
        # Classificar o erro
        error_type = self.classify_error(error_message, exception)
        severity = self.determine_severity(error_type, execution)
        
        # Determinar se é recuperável
        retry_strategy = self.retry_strategies.get(error_type, {})
        max_retries = retry_strategy.get("max_retries", 0)
        recoverable = max_retries > 0
        
        # Criar objeto de erro
        execution_error = ExecutionError(
            error_type=error_type,
            message=error_message,
            severity=severity,
            details=additional_details or {},
            recoverable=recoverable,
            retry_count=0,
            max_retries=max_retries,
            agent_id=agent_id,
            step_name=step_name
        )
        
        # Log do erro
        await self._log_error(execution, execution_error)
        
        # Notificar via WebSocket
        await self._notify_error_via_websocket(execution, execution_error)
        
        # Criar notificação
        await self._create_error_notification(execution, execution_error)
        
        # Decidir próxima ação
        if execution_error.can_retry():
            await self._schedule_retry(execution, execution_error)
        else:
            await self._mark_execution_failed(execution, execution_error)
        
        return execution_error

    async def _log_error(self, execution: TeamExecution, error: ExecutionError):
        """Registra o erro nos logs"""
        log_level = {
            ExecutionErrorSeverity.LOW: logging.INFO,
            ExecutionErrorSeverity.MEDIUM: logging.WARNING,
            ExecutionErrorSeverity.HIGH: logging.ERROR,
            ExecutionErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"Execution error in {execution.id}: {error.error_type.value} - {error.message}",
            extra={
                "execution_id": execution.id,
                "team_id": execution.team_id,
                "error_type": error.error_type.value,
                "severity": error.severity.value,
                "agent_id": error.agent_id,
                "step_name": error.step_name,
                "details": error.details,
                "stack_trace": error.stack_trace
            }
        )

    async def _notify_error_via_websocket(self, execution: TeamExecution, error: ExecutionError):
        """Notifica o erro via WebSocket"""
        error_data = {
            "type": "execution_error",
            "execution_id": execution.id,
            "team_id": execution.team_id,
            "error": error.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notificar canal da execução
        await self.websocket_manager.broadcast_to_channel(
            f"execution_{execution.id}",
            error_data
        )
        
        # Notificar canal da equipe
        await self.websocket_manager.broadcast_to_channel(
            f"team_{execution.team_id}",
            error_data
        )
        
        # Notificar usuário criador
        if execution.created_by:
            await self.websocket_manager.send_to_user(
                execution.created_by,
                error_data
            )

    async def _create_error_notification(self, execution: TeamExecution, error: ExecutionError):
        """Cria notificação para o erro"""
        if not execution.created_by:
            return
        
        title = f"Erro na execução - {error.error_type.value.replace('_', ' ').title()}"
        message = f"Execução da equipe falhou: {error.message}"
        
        if error.can_retry():
            message += f" (Tentativa {error.retry_count + 1}/{error.max_retries + 1})"
        
        await self.notification_service.create_notification(
            user_id=execution.created_by,
            title=title,
            message=message,
            notification_type=NotificationType.EXECUTION_FAILED,
            metadata={
                "execution_id": execution.id,
                "team_id": execution.team_id,
                "error_type": error.error_type.value,
                "severity": error.severity.value,
                "recoverable": error.recoverable,
                "retry_count": error.retry_count,
                "max_retries": error.max_retries
            }
        )

    async def _schedule_retry(self, execution: TeamExecution, error: ExecutionError):
        """Agenda uma nova tentativa de execução"""
        retry_strategy = self.retry_strategies.get(error.error_type, {})
        delay_seconds = retry_strategy.get("delay_seconds", [60])
        
        # Calcular delay baseado no número de tentativas
        if error.retry_count < len(delay_seconds):
            delay = delay_seconds[error.retry_count]
        else:
            delay = delay_seconds[-1]  # Usar o último delay se exceder a lista
        
        # Aplicar backoff exponencial se configurado
        if retry_strategy.get("exponential_backoff", False):
            delay = delay * (2 ** error.retry_count)
        
        logger.info(
            f"Scheduling retry for execution {execution.id} in {delay} seconds "
            f"(attempt {error.retry_count + 1}/{error.max_retries})"
        )
        
        # Aqui você implementaria a lógica para agendar o retry
        # Por exemplo, usando Celery, RQ ou outro sistema de filas
        # Por enquanto, apenas logamos a intenção
        
        # Atualizar status da execução
        execution.status = ExecutionStatus.PENDING
        execution.error_message = f"Retry scheduled: {error.message}"
        execution.retry_count = error.retry_count + 1
        
        # Notificar sobre o retry
        retry_data = {
            "type": "execution_retry_scheduled",
            "execution_id": execution.id,
            "team_id": execution.team_id,
            "retry_count": error.retry_count + 1,
            "max_retries": error.max_retries,
            "delay_seconds": delay,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_channel(
            f"execution_{execution.id}",
            retry_data
        )

    async def _mark_execution_failed(self, execution: TeamExecution, error: ExecutionError):
        """Marca a execução como falhada definitivamente"""
        execution.status = ExecutionStatus.FAILED
        execution.error_message = error.message
        execution.completed_at = datetime.utcnow()
        
        logger.error(
            f"Execution {execution.id} marked as failed: {error.error_type.value} - {error.message}"
        )
        
        # Notificar falha definitiva
        failure_data = {
            "type": "execution_failed_final",
            "execution_id": execution.id,
            "team_id": execution.team_id,
            "error": error.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_channel(
            f"execution_{execution.id}",
            failure_data
        )
        
        await self.websocket_manager.broadcast_to_channel(
            f"team_{execution.team_id}",
            failure_data
        )

    def get_error_recovery_suggestions(self, error: ExecutionError) -> List[str]:
        """Retorna sugestões de recuperação para o erro"""
        suggestions = {
            ExecutionErrorType.AGENT_TIMEOUT: [
                "Verifique a conectividade de rede",
                "Considere aumentar o timeout do agente",
                "Verifique se o agente está sobrecarregado"
            ],
            ExecutionErrorType.NETWORK_ERROR: [
                "Verifique a conexão com a internet",
                "Teste a conectividade com os serviços externos",
                "Considere usar um proxy ou VPN"
            ],
            ExecutionErrorType.AUTHENTICATION_ERROR: [
                "Verifique as credenciais de autenticação",
                "Confirme se os tokens não expiraram",
                "Verifique as permissões do usuário"
            ],
            ExecutionErrorType.RESOURCE_EXHAUSTED: [
                "Libere recursos do sistema",
                "Considere executar em horário de menor carga",
                "Otimize o uso de memória/CPU"
            ],
            ExecutionErrorType.INVALID_INPUT: [
                "Verifique os dados de entrada",
                "Confirme o formato dos parâmetros",
                "Valide os tipos de dados"
            ],
            ExecutionErrorType.DEPENDENCY_ERROR: [
                "Verifique se todas as dependências estão instaladas",
                "Confirme as versões das bibliotecas",
                "Reinstale as dependências se necessário"
            ],
            ExecutionErrorType.QUOTA_EXCEEDED: [
                "Aguarde o reset da cota",
                "Considere usar uma conta diferente",
                "Otimize o uso de recursos"
            ]
        }
        
        return suggestions.get(error.error_type, ["Contate o suporte técnico"])

    async def get_execution_error_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """Retorna o histórico de erros de uma execução"""
        # Esta função seria implementada para buscar erros do banco de dados
        # Por enquanto, retorna uma lista vazia
        return []

    async def get_error_statistics(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Retorna estatísticas de erros"""
        # Esta função seria implementada para calcular estatísticas do banco
        # Por enquanto, retorna estatísticas mock
        return {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_severity": {},
            "recovery_rate": 0.0,
            "most_common_errors": []
        }