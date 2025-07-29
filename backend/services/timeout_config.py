"""
Service-specific timeout configurations for Suna backend.

This module provides timeout configurations for different services
and utilities to apply them consistently across the application.
"""

import os
from typing import Dict, Any, Optional
from logging_config import get_logger
from config.timeout_settings import get_timeout_config, timeout_settings

logger = get_logger(__name__)


class TimeoutManager:
    """Manages timeout configurations for different services."""
    
    def __init__(self):
        self.timeout_settings = timeout_settings
        logger.info("TimeoutManager initialized", extra={
            "environment": self.timeout_settings.environment.value
        })
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis client configuration with timeouts."""
        config = get_timeout_config("redis")
        return {
            "socket_connect_timeout": config.get("connection_timeout", 5.0),
            "socket_timeout": config.get("socket_timeout", 10.0),
            "retry_on_timeout": config.get("retry_on_timeout", True),
            "socket_keepalive": config.get("socket_keepalive", True),
            "health_check_interval": config.get("health_check_interval", 30.0)
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database client configuration with timeouts."""
        config = get_timeout_config("database")
        return {
            "connect_timeout": config.get("connection_timeout", 10.0),
            "command_timeout": config.get("query_timeout", 30.0),
            "pool_timeout": config.get("pool_timeout", 5.0),
            "idle_timeout": config.get("idle_timeout", 300.0),
            "max_lifetime": config.get("max_lifetime", 3600.0)
        }
    
    def get_http_client_config(self) -> Dict[str, Any]:
        """Get HTTP client configuration with timeouts."""
        config = get_timeout_config("http_client")
        return {
            "timeout": {
                "connect": config.get("connect_timeout", 10.0),
                "read": config.get("read_timeout", 30.0),
                "write": config.get("read_timeout", 30.0),
                "pool": config.get("pool_timeout", 5.0)
            },
            "limits": {
                "max_keepalive_connections": 20,
                "max_connections": 100,
                "keepalive_expiry": 5.0
            }
        }
    
    def get_worker_config(self) -> Dict[str, Any]:
        """Get worker configuration with timeouts."""
        config = get_timeout_config("worker")
        return {
            "task_timeout": config.get("task_timeout", 300.0),
            "shutdown_timeout": config.get("shutdown_timeout", 30.0),
            "heartbeat_interval": config.get("heartbeat_interval", 60.0),
            "max_retries": config.get("max_retries", 3),
            "retry_delay": config.get("retry_delay", 5.0)
        }
    
    def get_rabbitmq_config(self) -> Dict[str, Any]:
        """Get RabbitMQ configuration with timeouts."""
        config = get_timeout_config("rabbitmq")
        return {
            "connection_timeout": config.get("connection_timeout", 10.0),
            "heartbeat": config.get("heartbeat", 600),
            "blocked_connection_timeout": config.get("blocked_connection_timeout", 300),
            "socket_timeout": config.get("socket_timeout", 5.0)
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration with timeouts."""
        config = get_timeout_config("api")
        return {
            "request_timeout": config.get("request_timeout", 120.0),
            "graceful_shutdown": config.get("graceful_shutdown", 30.0),
            "keep_alive": config.get("keep_alive", 2.0),
            "client_timeout": config.get("client_timeout", 60.0),
            "websocket_timeout": config.get("websocket_timeout", 300.0)
        }


# Global timeout manager instance
timeout_manager = TimeoutManager()


def apply_redis_timeouts(redis_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply Redis timeout configuration."""
    timeouts = timeout_manager.get_redis_config()
    redis_config.update(timeouts)
    logger.info("Applied Redis timeout configuration", extra={"timeouts": timeouts})
    return redis_config


def apply_database_timeouts(db_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply database timeout configuration."""
    timeouts = timeout_manager.get_database_config()
    db_config.update(timeouts)
    logger.info("Applied database timeout configuration", extra={"timeouts": timeouts})
    return db_config


def apply_http_timeouts(http_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply HTTP client timeout configuration."""
    timeouts = timeout_manager.get_http_client_config()
    http_config.update(timeouts)
    logger.info("Applied HTTP client timeout configuration", extra={"timeouts": timeouts})
    return http_config


def apply_worker_timeouts(worker_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply worker timeout configuration."""
    timeouts = timeout_manager.get_worker_config()
    worker_config.update(timeouts)
    logger.info("Applied worker timeout configuration", extra={"timeouts": timeouts})
    return worker_config


def validate_timeout_configuration():
    """Validate that all timeout configurations are reasonable."""
    return timeout_settings.validate_settings()


def log_timeout_summary():
    """Log a summary of all timeout configurations."""
    timeout_settings.log_settings_summary()


# Initialize and validate on import
if __name__ != "__main__":
    validate_timeout_configuration()
    log_timeout_summary()