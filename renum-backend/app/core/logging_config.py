"""
Standardized logging configuration for Renum backend.

This module provides consistent logging setup with structured logging,
proper formatting, and configurable levels.
"""

import logging
import logging.config
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
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
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        if hasattr(record, 'team_id'):
            log_data['team_id'] = record.team_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def get_logging_config() -> Dict[str, Any]:
    """Get standardized logging configuration for Renum."""
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Use JSON formatting in production, simple in development
    if environment == "production":
        formatter_class = "app.core.logging_config.JSONFormatter"
        format_string = ""
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "class": formatter_class,
                "format": format_string
            },
            "detailed": {
                "class": "logging.Formatter",
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
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "error_console"],
                "propagate": False
            },
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "gunicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "supabase": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "websocket": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    return config


def setup_logging():
    """Setup standardized logging for Renum backend."""
    
    # Apply logging configuration
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Set up root logger
    logger = logging.getLogger(__name__)
    logger.info("Renum logging configuration initialized", extra={
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "environment": os.getenv("ENVIRONMENT", "development")
    })
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


# Timeout configurations for Renum services
RENUM_TIMEOUT_CONFIG = {
    "http_client": {
        "connect_timeout": 10.0,
        "read_timeout": 30.0,
        "total_timeout": 60.0
    },
    "database": {
        "connection_timeout": 10.0,
        "query_timeout": 30.0,
        "transaction_timeout": 60.0
    },
    "redis": {
        "connection_timeout": 5.0,
        "socket_timeout": 10.0,
        "health_check_interval": 30.0
    },
    "websocket": {
        "connection_timeout": 30.0,
        "message_timeout": 10.0,
        "ping_interval": 20.0,
        "ping_timeout": 10.0
    },
    "team_execution": {
        "task_timeout": 600.0,  # 10 minutes
        "coordination_timeout": 30.0,
        "context_sync_timeout": 15.0
    },
    "api": {
        "request_timeout": 120.0,
        "graceful_shutdown": 30.0,
        "keep_alive": 2.0
    },
    "suna_integration": {
        "api_timeout": 60.0,
        "retry_timeout": 5.0,
        "max_retries": 3
    }
}


def get_timeout_config(service: str) -> Dict[str, float]:
    """Get timeout configuration for a specific Renum service."""
    return RENUM_TIMEOUT_CONFIG.get(service, {})


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()