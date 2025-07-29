"""
Decorators and utilities for instrumenting code with Prometheus metrics.

This module provides decorators and context managers to easily add
metrics collection to database operations, Redis operations, and business logic.
"""

import time
import asyncio
from functools import wraps
from contextlib import contextmanager, asynccontextmanager
from typing import Callable, Dict, Any, Optional, Union
from services.metrics import get_metrics_collector
from logging_config import get_logger

logger = get_logger(__name__)


def instrument_database_query(operation: str, table: str = "unknown"):
    """
    Decorator to instrument database queries with metrics.
    
    Args:
        operation: Type of database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Name of the table being queried
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="database"
                )
                logger.error(f"Database query failed: {operation} on {table}", extra={
                    "operation": operation,
                    "table": table,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_database_query(operation, table, status, duration)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="database"
                )
                logger.error(f"Database query failed: {operation} on {table}", extra={
                    "operation": operation,
                    "table": table,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_database_query(operation, table, status, duration)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def instrument_redis_operation(operation: str):
    """
    Decorator to instrument Redis operations with metrics.
    
    Args:
        operation: Type of Redis operation (GET, SET, DEL, etc.)
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="redis"
                )
                logger.error(f"Redis operation failed: {operation}", extra={
                    "operation": operation,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_redis_operation(operation, status, duration)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="redis"
                )
                logger.error(f"Redis operation failed: {operation}", extra={
                    "operation": operation,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_redis_operation(operation, status, duration)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def instrument_worker_task(task_name: str):
    """
    Decorator to instrument worker tasks with metrics.
    
    Args:
        task_name: Name of the worker task
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="worker"
                )
                logger.error(f"Worker task failed: {task_name}", extra={
                    "task_name": task_name,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_worker_task(task_name, status, duration)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="worker"
                )
                logger.error(f"Worker task failed: {task_name}", extra={
                    "task_name": task_name,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_worker_task(task_name, status, duration)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def instrument_agent_execution(agent_type: str):
    """
    Decorator to instrument agent executions with metrics.
    
    Args:
        agent_type: Type of agent being executed
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="agent"
                )
                logger.error(f"Agent execution failed: {agent_type}", extra={
                    "agent_type": agent_type,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_agent_execution(agent_type, status, duration)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="agent"
                )
                logger.error(f"Agent execution failed: {agent_type}", extra={
                    "agent_type": agent_type,
                    "error": str(e)
                })
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_agent_execution(agent_type, status, duration)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def instrument_llm_request(provider: str, model: str):
    """
    Decorator to instrument LLM requests with metrics.
    
    Args:
        provider: LLM provider (openai, anthropic, etc.)
        model: Model name
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                
                # Try to extract token usage from result
                input_tokens = 0
                output_tokens = 0
                
                if isinstance(result, dict):
                    usage = result.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                
                duration = time.time() - start_time
                metrics.record_llm_request(
                    provider, model, status, duration, input_tokens, output_tokens
                )
                
                return result
            except Exception as e:
                status = "error"
                duration = time.time() - start_time
                metrics.record_llm_request(provider, model, status, duration)
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="llm"
                )
                logger.error(f"LLM request failed: {provider}/{model}", extra={
                    "provider": provider,
                    "model": model,
                    "error": str(e)
                })
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Try to extract token usage from result
                input_tokens = 0
                output_tokens = 0
                
                if isinstance(result, dict):
                    usage = result.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                
                duration = time.time() - start_time
                metrics.record_llm_request(
                    provider, model, status, duration, input_tokens, output_tokens
                )
                
                return result
            except Exception as e:
                status = "error"
                duration = time.time() - start_time
                metrics.record_llm_request(provider, model, status, duration)
                metrics.record_error(
                    error_type=type(e).__name__,
                    component="llm"
                )
                logger.error(f"LLM request failed: {provider}/{model}", extra={
                    "provider": provider,
                    "model": model,
                    "error": str(e)
                })
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context managers for manual instrumentation

@contextmanager
def time_database_operation(operation: str, table: str = "unknown"):
    """Context manager to time database operations."""
    metrics = get_metrics_collector()
    with metrics.time_database_query(operation, table):
        yield


@contextmanager
def time_redis_operation(operation: str):
    """Context manager to time Redis operations."""
    metrics = get_metrics_collector()
    with metrics.time_redis_operation(operation):
        yield


@contextmanager
def time_worker_task(task_name: str):
    """Context manager to time worker tasks."""
    metrics = get_metrics_collector()
    with metrics.time_worker_task(task_name):
        yield


# Async context managers

@asynccontextmanager
async def time_async_operation(operation_type: str, **labels):
    """Generic async context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"Async operation {operation_type} completed", extra={
            "operation_type": operation_type,
            "duration": duration,
            **labels
        })


# Utility functions for manual metrics recording

def record_business_metric(metric_name: str, value: Union[int, float], labels: Dict[str, str] = None):
    """Record a custom business metric."""
    metrics = get_metrics_collector()
    
    # This is a simplified version - in practice, you'd want to have
    # predefined business metrics or a way to register custom metrics
    logger.info(f"Business metric recorded: {metric_name}", extra={
        "metric_name": metric_name,
        "value": value,
        "labels": labels or {}
    })


def update_system_gauge(gauge_name: str, value: Union[int, float], labels: Dict[str, str] = None):
    """Update a system gauge metric."""
    metrics = get_metrics_collector()
    
    # Map common gauge names to actual metrics
    if gauge_name == "active_sessions":
        metrics.update_active_sessions(int(value))
    elif gauge_name == "database_connections":
        # This would need additional parameters for pool_size
        pass
    else:
        logger.debug(f"System gauge updated: {gauge_name}", extra={
            "gauge_name": gauge_name,
            "value": value,
            "labels": labels or {}
        })


def increment_counter(counter_name: str, labels: Dict[str, str] = None, amount: int = 1):
    """Increment a counter metric."""
    logger.debug(f"Counter incremented: {counter_name}", extra={
        "counter_name": counter_name,
        "amount": amount,
        "labels": labels or {}
    })


# Health check utilities

def check_metrics_health() -> Dict[str, Any]:
    """Check the health of the metrics system."""
    try:
        metrics = get_metrics_collector()
        metrics_data = metrics.get_metrics()
        
        return {
            "status": "healthy",
            "metrics_available": True,
            "metrics_size": len(metrics_data),
            "collectors_count": len(metrics.registry._collector_to_names)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "metrics_available": False,
            "error": str(e),
            "error_type": type(e).__name__
        }