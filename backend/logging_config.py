"""
Standardized logging configuration for Suna backend services.

This module provides consistent logging setup across all backend services
with structured logging, proper formatting, and configurable levels.
"""

import logging
import logging.config
import logging.handlers
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record):
        """Format log record with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread
        }
        
        # Add extra fields if present
        extra_fields = [
            'user_id', 'request_id', 'execution_time', 'service_name',
            'endpoint', 'method', 'status_code', 'duration', 'error_type',
            'client_ip', 'user_agent', 'correlation_id', 'trace_id'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add stack info if present
        if record.stack_info:
            log_data['stack_info'] = record.stack_info
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format with colors for console output."""
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def get_logging_config() -> Dict[str, Any]:
    """Get standardized logging configuration."""
    try:
        from config.logging_settings import get_logging_config as get_config
        return get_config()
    except ImportError:
        # Fallback configuration if logging_settings is not available
        return _get_fallback_logging_config()


def _get_fallback_logging_config() -> Dict[str, Any]:
    """Get fallback logging configuration."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "structured")  # structured, simple, or colored
    environment = os.getenv("ENVIRONMENT", "development")  # development or production
    
    # Determine formatter based on format and environment
    if log_format == "structured":
        formatter_class = "logging_config.StructuredFormatter"
        format_string = ""
    elif log_format == "colored" and environment == "development":
        formatter_class = "logging_config.ColoredFormatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "class": formatter_class,
                "format": format_string
            },
            "detailed": {
                "class": formatter_class,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "stream": "ext://sys.stderr"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": "logs/access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "file", "error_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "access_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "gunicorn": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "gunicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["console", "error_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "supabase": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "dramatiq": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "rabbitmq": {
                "level": "WARNING",
                "handlers": ["console", "error_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "error_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "websockets": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "sentry": {
                "level": "WARNING",
                "handlers": ["console", "error_file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "timeout": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            },
            "middleware": {
                "level": "INFO",
                "handlers": ["console", "file"] if environment == "production" else ["console"],
                "propagate": False
            }
        }
    }
    
    return config


def setup_logging():
    """Setup standardized logging for the application."""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Apply logging configuration
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Configure structlog if using structured logging
    if os.getenv("LOG_FORMAT", "structured") == "structured":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Set up root logger
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized", extra={
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_format": os.getenv("LOG_FORMAT", "structured")
    })
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def get_contextual_logger(name: str, **context) -> logging.LoggerAdapter:
    """Get a logger with additional context."""
    logger = get_logger(name)
    return logging.LoggerAdapter(logger, context)


def log_request_info(logger: logging.Logger, request_id: str, method: str, 
                    path: str, user_id: Optional[str] = None, **kwargs):
    """Log request information with consistent format."""
    logger.info("Request started", extra={
        "request_id": request_id,
        "method": method,
        "path": path,
        "user_id": user_id,
        **kwargs
    })


def log_request_completion(logger: logging.Logger, request_id: str, 
                          status_code: int, duration: float, **kwargs):
    """Log request completion with consistent format."""
    logger.info("Request completed", extra={
        "request_id": request_id,
        "status_code": status_code,
        "duration": duration,
        **kwargs
    })


def log_error_with_context(logger: logging.Logger, error: Exception, 
                          context: Dict[str, Any]):
    """Log error with additional context."""
    logger.error(f"Error occurred: {str(error)}", extra={
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context
    }, exc_info=True)


def get_timeout_config(service: str) -> Dict[str, float]:
    """Get timeout configuration for a specific service."""
    try:
        from config.timeout_settings import get_timeout_config as get_config
        return get_config(service)
    except ImportError:
        # Fallback configuration if timeout_settings is not available
        fallback_config = {
            "http_client": {
                "connect_timeout": 10.0,
                "read_timeout": 30.0,
                "total_timeout": 60.0,
                "pool_timeout": 5.0,
                "max_retries": 3
            },
            "database": {
                "connection_timeout": 10.0,
                "query_timeout": 30.0,
                "transaction_timeout": 60.0,
                "pool_timeout": 5.0,
                "idle_timeout": 300.0,
                "max_lifetime": 3600.0
            },
            "redis": {
                "connection_timeout": 5.0,
                "socket_timeout": 10.0,
                "health_check_interval": 30.0,
                "retry_on_timeout": True,
                "socket_keepalive": True
            },
            "worker": {
                "task_timeout": 300.0,
                "shutdown_timeout": 30.0,
                "heartbeat_interval": 60.0,
                "max_retries": 3,
                "retry_delay": 5.0
            },
            "api": {
                "request_timeout": 120.0,
                "graceful_shutdown": 30.0,
                "keep_alive": 2.0,
                "client_timeout": 60.0,
                "websocket_timeout": 300.0
            },
            "rabbitmq": {
                "connection_timeout": 10.0,
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
                "socket_timeout": 5.0
            }
        }
        return fallback_config.get(service, {})


def apply_timeout_to_client(client_type: str, client_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply timeout configuration to client configuration."""
    timeout_config = get_timeout_config(client_type)
    if not timeout_config:
        return client_config
    
    # Apply timeouts based on client type
    if client_type == "redis":
        client_config.update({
            "socket_connect_timeout": timeout_config.get("connection_timeout", 5.0),
            "socket_timeout": timeout_config.get("socket_timeout", 10.0),
            "retry_on_timeout": timeout_config.get("retry_on_timeout", True),
            "socket_keepalive": timeout_config.get("socket_keepalive", True),
            "health_check_interval": timeout_config.get("health_check_interval", 30.0)
        })
    elif client_type == "database":
        client_config.update({
            "connect_timeout": timeout_config.get("connection_timeout", 10.0),
            "command_timeout": timeout_config.get("query_timeout", 30.0),
            "pool_timeout": timeout_config.get("pool_timeout", 5.0)
        })
    elif client_type == "http_client":
        client_config.update({
            "timeout": {
                "connect": timeout_config.get("connect_timeout", 10.0),
                "read": timeout_config.get("read_timeout", 30.0),
                "total": timeout_config.get("total_timeout", 60.0),
                "pool": timeout_config.get("pool_timeout", 5.0)
            }
        })
    
    return client_config


def setup_service_timeouts():
    """Setup timeout configurations for all services."""
    logger = get_logger(__name__)
    
    try:
        from config.timeout_settings import get_all_timeout_settings, log_timeout_summary
        log_timeout_summary()
        return get_all_timeout_settings()
    except ImportError:
        logger.warning("timeout_settings module not available, using fallback configuration")
        return {}


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()