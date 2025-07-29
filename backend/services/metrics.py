"""
Prometheus metrics service for Suna backend.

This module provides comprehensive metrics collection for monitoring
HTTP requests, database operations, Redis operations, and business logic.
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from logging_config import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Centralized metrics collector for all Suna services."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()
        logger.info("Metrics collector initialized")
    
    def _setup_metrics(self):
        """Setup all Prometheus metrics."""
        
        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.http_request_size_bytes = Histogram(
            'http_request_size_bytes',
            'HTTP request size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.http_response_size_bytes = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Database Metrics
        self.database_queries_total = Counter(
            'database_queries_total',
            'Total number of database queries',
            ['operation', 'table', 'status'],
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.database_connections_pool_size = Gauge(
            'database_connections_pool_size',
            'Database connection pool size',
            registry=self.registry
        )
        
        # Redis Metrics
        self.redis_operations_total = Counter(
            'redis_operations_total',
            'Total number of Redis operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.redis_operation_duration_seconds = Histogram(
            'redis_operation_duration_seconds',
            'Redis operation duration in seconds',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry
        )
        
        self.redis_connections_active = Gauge(
            'redis_connections_active',
            'Number of active Redis connections',
            registry=self.registry
        )
        
        self.redis_memory_usage_bytes = Gauge(
            'redis_memory_usage_bytes',
            'Redis memory usage in bytes',
            registry=self.registry
        )
        
        # Worker/Queue Metrics
        self.worker_tasks_total = Counter(
            'worker_tasks_total',
            'Total number of worker tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.worker_task_duration_seconds = Histogram(
            'worker_task_duration_seconds',
            'Worker task duration in seconds',
            ['task_name'],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self.registry
        )
        
        self.worker_queue_size = Gauge(
            'worker_queue_size',
            'Number of tasks in worker queue',
            ['queue_name'],
            registry=self.registry
        )
        
        # Business Logic Metrics
        self.user_sessions_active = Gauge(
            'user_sessions_active',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.agent_executions_total = Counter(
            'agent_executions_total',
            'Total number of agent executions',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.agent_execution_duration_seconds = Histogram(
            'agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
            registry=self.registry
        )
        
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.llm_request_duration_seconds = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider', 'model'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total number of LLM tokens used',
            ['provider', 'model', 'type'],  # type: input/output
            registry=self.registry
        )
        
        # System Metrics
        self.application_info = Info(
            'application_info',
            'Application information',
            registry=self.registry
        )
        
        self.application_status = Enum(
            'application_status',
            'Application status',
            states=['starting', 'healthy', 'degraded', 'unhealthy'],
            registry=self.registry
        )
        
        # Error Metrics
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Set application info
        self.application_info.info({
            'version': '1.0.0',
            'environment': 'development',  # This should come from config
            'service': 'suna-backend'
        })
        
        self.application_status.state('healthy')
    
    # HTTP Metrics Methods
    def record_http_request(self, method: str, endpoint: str, status_code: int, 
                           duration: float, request_size: int = 0, response_size: int = 0):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            self.http_request_size_bytes.labels(
                method=method, 
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            self.http_response_size_bytes.labels(
                method=method, 
                endpoint=endpoint
            ).observe(response_size)
    
    @contextmanager
    def time_http_request(self, method: str, endpoint: str):
        """Context manager to time HTTP requests."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            # Note: status_code will be recorded separately
            self.http_request_duration_seconds.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
    
    # Database Metrics Methods
    def record_database_query(self, operation: str, table: str, status: str, duration: float):
        """Record database query metrics."""
        self.database_queries_total.labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
        
        self.database_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    @contextmanager
    def time_database_query(self, operation: str, table: str):
        """Context manager to time database queries."""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "error"
            logger.error(f"Database query failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.record_database_query(operation, table, status, duration)
    
    def update_database_connections(self, active: int, pool_size: int):
        """Update database connection metrics."""
        self.database_connections_active.set(active)
        self.database_connections_pool_size.set(pool_size)
    
    # Redis Metrics Methods
    def record_redis_operation(self, operation: str, status: str, duration: float):
        """Record Redis operation metrics."""
        self.redis_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        self.redis_operation_duration_seconds.labels(
            operation=operation
        ).observe(duration)
    
    @contextmanager
    def time_redis_operation(self, operation: str):
        """Context manager to time Redis operations."""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "error"
            logger.error(f"Redis operation failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.record_redis_operation(operation, status, duration)
    
    def update_redis_metrics(self, active_connections: int, memory_usage: int):
        """Update Redis system metrics."""
        self.redis_connections_active.set(active_connections)
        self.redis_memory_usage_bytes.set(memory_usage)
    
    # Worker Metrics Methods
    def record_worker_task(self, task_name: str, status: str, duration: float):
        """Record worker task metrics."""
        self.worker_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        self.worker_task_duration_seconds.labels(
            task_name=task_name
        ).observe(duration)
    
    @contextmanager
    def time_worker_task(self, task_name: str):
        """Context manager to time worker tasks."""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "error"
            logger.error(f"Worker task failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.record_worker_task(task_name, status, duration)
    
    def update_queue_size(self, queue_name: str, size: int):
        """Update worker queue size."""
        self.worker_queue_size.labels(queue_name=queue_name).set(size)
    
    # Business Logic Metrics Methods
    def update_active_sessions(self, count: int):
        """Update active user sessions count."""
        self.user_sessions_active.set(count)
    
    def record_agent_execution(self, agent_type: str, status: str, duration: float):
        """Record agent execution metrics."""
        self.agent_executions_total.labels(
            agent_type=agent_type,
            status=status
        ).inc()
        
        self.agent_execution_duration_seconds.labels(
            agent_type=agent_type
        ).observe(duration)
    
    def record_llm_request(self, provider: str, model: str, status: str, 
                          duration: float, input_tokens: int = 0, output_tokens: int = 0):
        """Record LLM request metrics."""
        self.llm_requests_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        self.llm_request_duration_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration)
        
        if input_tokens > 0:
            self.llm_tokens_total.labels(
                provider=provider,
                model=model,
                type="input"
            ).inc(input_tokens)
        
        if output_tokens > 0:
            self.llm_tokens_total.labels(
                provider=provider,
                model=model,
                type="output"
            ).inc(output_tokens)
    
    # Error Metrics Methods
    def record_error(self, error_type: str, component: str):
        """Record error occurrence."""
        self.errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    # System Status Methods
    def set_application_status(self, status: str):
        """Set application status."""
        if status in ['starting', 'healthy', 'degraded', 'unhealthy']:
            self.application_status.state(status)
        else:
            logger.warning(f"Invalid application status: {status}")
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode('utf-8')


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector


# Decorator for timing functions
def time_function(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to time function execution."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # This is a simplified version - in practice, you'd want to
                # use the appropriate metric based on the function type
                logger.debug(f"Function {func.__name__} took {duration:.3f}s")
        return wrapper
    return decorator


# Async decorator for timing async functions
def time_async_function(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to time async function execution."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.debug(f"Async function {func.__name__} took {duration:.3f}s")
        return wrapper
    return decorator