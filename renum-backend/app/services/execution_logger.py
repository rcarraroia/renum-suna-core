"""
Sistema de logs detalhados para execuções
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from app.models.team_models import TeamExecution
from app.services.websocket_manager import WebSocketManager

class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(Enum):
    """Categorias de log"""
    EXECUTION = "execution"
    AGENT = "agent"
    NETWORK = "network"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    PERFORMANCE = "performance"

class ExecutionLogEntry:
    """Entrada de log de execução"""
    
    def __init__(
        self,
        execution_id: str,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        step_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        correlation_id: Optional[str] = None
    ):
        self.execution_id = execution_id
        self.level = level
        self.category = category
        self.message = message
        self.details = details or {}
        self.agent_id = agent_id
        self.step_name = step_name
        self.timestamp = timestamp or datetime.utcnow()
        self.correlation_id = correlation_id

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "execution_id": self.execution_id,
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "agent_id": self.agent_id,
            "step_name": self.step_name,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id
        }

class ExecutionLogger:
    """Logger especializado para execuções"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        self.log_buffer: Dict[str, List[ExecutionLogEntry]] = {}
        self.max_buffer_size = 1000

    async def log(
        self,
        execution_id: str,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        step_name: Optional[str] = None,
        correlation_id: Optional[str] = None,
        broadcast: bool = True
    ):
        """Registra uma entrada de log"""
        
        log_entry = ExecutionLogEntry(
            execution_id=execution_id,
            level=level,
            category=category,
            message=message,
            details=details,
            agent_id=agent_id,
            step_name=step_name,
            correlation_id=correlation_id
        )
        
        # Adicionar ao buffer
        if execution_id not in self.log_buffer:
            self.log_buffer[execution_id] = []
        
        self.log_buffer[execution_id].append(log_entry)
        
        # Limitar tamanho do buffer
        if len(self.log_buffer[execution_id]) > self.max_buffer_size:
            self.log_buffer[execution_id] = self.log_buffer[execution_id][-self.max_buffer_size:]
        
        # Log no sistema padrão
        python_level = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.INFO)
        
        self.logger.log(
            python_level,
            f"[{execution_id}] [{category.value}] {message}",
            extra={
                "execution_id": execution_id,
                "category": category.value,
                "agent_id": agent_id,
                "step_name": step_name,
                "details": details,
                "correlation_id": correlation_id
            }
        )
        
        # Broadcast via WebSocket se solicitado
        if broadcast:
            await self._broadcast_log_entry(log_entry)

    async def _broadcast_log_entry(self, log_entry: ExecutionLogEntry):
        """Faz broadcast da entrada de log via WebSocket"""
        log_data = {
            "type": "execution_log",
            "log_entry": log_entry.to_dict()
        }
        
        # Enviar para canal da execução
        await self.websocket_manager.broadcast_to_channel(
            f"execution_{log_entry.execution_id}",
            log_data
        )
        
        # Enviar para canal de logs (para debugging)
        await self.websocket_manager.broadcast_to_channel(
            f"execution_logs_{log_entry.execution_id}",
            log_data
        )

    async def debug(
        self,
        execution_id: str,
        message: str,
        category: LogCategory = LogCategory.EXECUTION,
        **kwargs
    ):
        """Log de debug"""
        await self.log(execution_id, LogLevel.DEBUG, category, message, **kwargs)

    async def info(
        self,
        execution_id: str,
        message: str,
        category: LogCategory = LogCategory.EXECUTION,
        **kwargs
    ):
        """Log de informação"""
        await self.log(execution_id, LogLevel.INFO, category, message, **kwargs)

    async def warning(
        self,
        execution_id: str,
        message: str,
        category: LogCategory = LogCategory.EXECUTION,
        **kwargs
    ):
        """Log de aviso"""
        await self.log(execution_id, LogLevel.WARNING, category, message, **kwargs)

    async def error(
        self,
        execution_id: str,
        message: str,
        category: LogCategory = LogCategory.EXECUTION,
        **kwargs
    ):
        """Log de erro"""
        await self.log(execution_id, LogLevel.ERROR, category, message, **kwargs)

    async def critical(
        self,
        execution_id: str,
        message: str,
        category: LogCategory = LogCategory.EXECUTION,
        **kwargs
    ):
        """Log crítico"""
        await self.log(execution_id, LogLevel.CRITICAL, category, message, **kwargs)

    # Métodos de conveniência para categorias específicas
    async def log_execution_start(
        self,
        execution_id: str,
        team_id: str,
        user_id: str,
        agents: List[str]
    ):
        """Log do início de execução"""
        await self.info(
            execution_id,
            f"Execution started for team {team_id}",
            category=LogCategory.EXECUTION,
            details={
                "team_id": team_id,
                "user_id": user_id,
                "agents": agents,
                "agent_count": len(agents)
            }
        )

    async def log_execution_complete(
        self,
        execution_id: str,
        duration_seconds: float,
        result: Optional[Any] = None
    ):
        """Log da conclusão de execução"""
        await self.info(
            execution_id,
            f"Execution completed in {duration_seconds:.2f} seconds",
            category=LogCategory.EXECUTION,
            details={
                "duration_seconds": duration_seconds,
                "result_size": len(str(result)) if result else 0,
                "has_result": result is not None
            }
        )

    async def log_execution_failed(
        self,
        execution_id: str,
        error_message: str,
        error_type: str,
        duration_seconds: Optional[float] = None
    ):
        """Log de falha na execução"""
        await self.error(
            execution_id,
            f"Execution failed: {error_message}",
            category=LogCategory.EXECUTION,
            details={
                "error_type": error_type,
                "duration_seconds": duration_seconds
            }
        )

    async def log_agent_start(
        self,
        execution_id: str,
        agent_id: str,
        step_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ):
        """Log do início de agente"""
        await self.info(
            execution_id,
            f"Agent {agent_id} started step '{step_name}'",
            category=LogCategory.AGENT,
            agent_id=agent_id,
            step_name=step_name,
            details={
                "input_size": len(str(input_data)) if input_data else 0,
                "has_input": input_data is not None
            }
        )

    async def log_agent_complete(
        self,
        execution_id: str,
        agent_id: str,
        step_name: str,
        duration_seconds: float,
        output_data: Optional[Dict[str, Any]] = None
    ):
        """Log da conclusão de agente"""
        await self.info(
            execution_id,
            f"Agent {agent_id} completed step '{step_name}' in {duration_seconds:.2f}s",
            category=LogCategory.AGENT,
            agent_id=agent_id,
            step_name=step_name,
            details={
                "duration_seconds": duration_seconds,
                "output_size": len(str(output_data)) if output_data else 0,
                "has_output": output_data is not None
            }
        )

    async def log_agent_error(
        self,
        execution_id: str,
        agent_id: str,
        step_name: str,
        error_message: str,
        error_type: str,
        duration_seconds: Optional[float] = None
    ):
        """Log de erro do agente"""
        await self.error(
            execution_id,
            f"Agent {agent_id} failed in step '{step_name}': {error_message}",
            category=LogCategory.AGENT,
            agent_id=agent_id,
            step_name=step_name,
            details={
                "error_type": error_type,
                "duration_seconds": duration_seconds
            }
        )

    async def log_network_request(
        self,
        execution_id: str,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        agent_id: Optional[str] = None
    ):
        """Log de requisição de rede"""
        message = f"{method} {url}"
        if status_code:
            message += f" -> {status_code}"
        if duration_ms:
            message += f" ({duration_ms:.0f}ms)"
        
        level = LogLevel.INFO
        if status_code and status_code >= 400:
            level = LogLevel.WARNING if status_code < 500 else LogLevel.ERROR
        
        await self.log(
            execution_id,
            level,
            LogCategory.NETWORK,
            message,
            agent_id=agent_id,
            details={
                "method": method,
                "url": url,
                "status_code": status_code,
                "duration_ms": duration_ms
            }
        )

    async def log_performance_metric(
        self,
        execution_id: str,
        metric_name: str,
        value: float,
        unit: str,
        agent_id: Optional[str] = None,
        step_name: Optional[str] = None
    ):
        """Log de métrica de performance"""
        await self.info(
            execution_id,
            f"Performance metric: {metric_name} = {value} {unit}",
            category=LogCategory.PERFORMANCE,
            agent_id=agent_id,
            step_name=step_name,
            details={
                "metric_name": metric_name,
                "value": value,
                "unit": unit
            }
        )

    async def log_user_action(
        self,
        execution_id: str,
        user_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log de ação do usuário"""
        await self.info(
            execution_id,
            f"User {user_id} performed action: {action}",
            category=LogCategory.USER_ACTION,
            details={
                "user_id": user_id,
                "action": action,
                **(details or {})
            }
        )

    def get_logs(
        self,
        execution_id: str,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ExecutionLogEntry]:
        """Obtém logs filtrados"""
        if execution_id not in self.log_buffer:
            return []
        
        logs = self.log_buffer[execution_id]
        
        # Aplicar filtros
        if level:
            logs = [log for log in logs if log.level == level]
        
        if category:
            logs = [log for log in logs if log.category == category]
        
        if agent_id:
            logs = [log for log in logs if log.agent_id == agent_id]
        
        # Aplicar limite
        if limit:
            logs = logs[-limit:]
        
        return logs

    def get_log_summary(self, execution_id: str) -> Dict[str, Any]:
        """Obtém resumo dos logs"""
        if execution_id not in self.log_buffer:
            return {
                "total_logs": 0,
                "by_level": {},
                "by_category": {},
                "by_agent": {},
                "first_log": None,
                "last_log": None
            }
        
        logs = self.log_buffer[execution_id]
        
        # Contar por nível
        by_level = {}
        for level in LogLevel:
            by_level[level.value] = len([log for log in logs if log.level == level])
        
        # Contar por categoria
        by_category = {}
        for category in LogCategory:
            by_category[category.value] = len([log for log in logs if log.category == category])
        
        # Contar por agente
        by_agent = {}
        for log in logs:
            if log.agent_id:
                by_agent[log.agent_id] = by_agent.get(log.agent_id, 0) + 1
        
        return {
            "total_logs": len(logs),
            "by_level": by_level,
            "by_category": by_category,
            "by_agent": by_agent,
            "first_log": logs[0].to_dict() if logs else None,
            "last_log": logs[-1].to_dict() if logs else None
        }

    def clear_logs(self, execution_id: str):
        """Limpa logs de uma execução"""
        if execution_id in self.log_buffer:
            del self.log_buffer[execution_id]

    def get_all_execution_ids(self) -> List[str]:
        """Obtém todos os IDs de execução com logs"""
        return list(self.log_buffer.keys())