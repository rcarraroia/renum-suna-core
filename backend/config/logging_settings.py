"""
Service-specific logging configurations for Suna backend.

This module provides logging configurations optimized for different
services and deployment environments.
"""

import os
from typing import Dict, Any, List
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """Log formats."""
    STRUCTURED = "structured"
    SIMPLE = "simple"
    COLORED = "colored"


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LoggingSettings:
    """Environment-specific logging configurations."""
    
    def __init__(self, environment: Environment = None):
        self.environment = environment or self._detect_environment()
        self.log_level = self._get_log_level()
        self.log_format = self._get_log_format()
        self.log_dir = self._get_log_directory()
        self._ensure_log_directory()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        if env_name in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env_name in ["stage", "staging"]:
            return Environment.STAGING
        else:
            return Environment.DEVELOPMENT
    
    def _get_log_level(self) -> LogLevel:
        """Get log level based on environment."""
        level_name = os.getenv("LOG_LEVEL", "").upper()
        
        # Environment-specific defaults
        if not level_name:
            if self.environment == Environment.PRODUCTION:
                level_name = "INFO"
            elif self.environment == Environment.STAGING:
                level_name = "INFO"
            else:
                level_name = "DEBUG"
        
        try:
            return LogLevel(level_name)
        except ValueError:
            return LogLevel.INFO
    
    def _get_log_format(self) -> LogFormat:
        """Get log format based on environment."""
        format_name = os.getenv("LOG_FORMAT", "").lower()
        
        # Environment-specific defaults
        if not format_name:
            if self.environment == Environment.PRODUCTION:
                format_name = "structured"
            elif self.environment == Environment.STAGING:
                format_name = "structured"
            else:
                format_name = "colored"
        
        try:
            return LogFormat(format_name)
        except ValueError:
            return LogFormat.STRUCTURED
    
    def _get_log_directory(self) -> Path:
        """Get log directory path."""
        log_dir = os.getenv("LOG_DIR", "logs")
        return Path(log_dir)
    
    def _ensure_log_directory(self):
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_service_logger_config(self, service_name: str) -> Dict[str, Any]:
        """Get logger configuration for a specific service."""
        
        # Service-specific log levels
        service_levels = {
            "uvicorn": LogLevel.INFO,
            "gunicorn": LogLevel.INFO,
            "fastapi": LogLevel.INFO,
            "redis": LogLevel.WARNING,
            "supabase": LogLevel.INFO,
            "dramatiq": LogLevel.INFO,
            "rabbitmq": LogLevel.WARNING,
            "httpx": LogLevel.WARNING,
            "websockets": LogLevel.INFO,
            "sentry": LogLevel.WARNING,
            "timeout": LogLevel.INFO,
            "middleware": LogLevel.INFO
        }
        
        service_level = service_levels.get(service_name, self.log_level)
        
        config = {
            "level": service_level.value,
            "handlers": self._get_handlers_for_service(service_name),
            "propagate": False
        }
        
        return config
    
    def _get_handlers_for_service(self, service_name: str) -> List[str]:
        """Get appropriate handlers for a service."""
        handlers = ["console"]
        
        if self.environment == Environment.PRODUCTION:
            handlers.extend(["file", "error_file"])
            
            # Access logs for web servers
            if service_name in ["uvicorn", "gunicorn"]:
                handlers.append("access_file")
        
        return handlers
    
    def get_handler_config(self, handler_name: str) -> Dict[str, Any]:
        """Get configuration for a specific handler."""
        
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "level": self.log_level.value,
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
                "level": self.log_level.value,
                "formatter": "detailed",
                "filename": str(self.log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(self.log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": str(self.log_dir / "access.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8"
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(self.log_dir / "debug.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8"
            }
        }
        
        return handlers.get(handler_name, {})
    
    def get_formatter_config(self, formatter_name: str) -> Dict[str, Any]:
        """Get configuration for a specific formatter."""
        
        if self.log_format == LogFormat.STRUCTURED:
            formatter_class = "logging_config.StructuredFormatter"
            format_string = ""
        elif self.log_format == LogFormat.COLORED and self.environment == Environment.DEVELOPMENT:
            formatter_class = "logging_config.ColoredFormatter"
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            formatter_class = "logging.Formatter"
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        
        formatters = {
            "standard": {
                "class": formatter_class,
                "format": format_string
            },
            "detailed": {
                "class": formatter_class,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
            },
            "simple": {
                "class": "logging.Formatter",
                "format": "%(levelname)s - %(message)s"
            }
        }
        
        return formatters.get(formatter_name, formatters["standard"])
    
    def get_complete_logging_config(self) -> Dict[str, Any]:
        """Get complete logging configuration dictionary."""
        
        # Define all services
        services = [
            "uvicorn", "uvicorn.access", "gunicorn", "gunicorn.access",
            "fastapi", "redis", "supabase", "dramatiq", "rabbitmq",
            "httpx", "websockets", "sentry", "timeout", "middleware"
        ]
        
        # Build handlers configuration
        handler_names = ["console", "error_console", "file", "error_file", "access_file"]
        if self.environment == Environment.DEVELOPMENT:
            handler_names.append("debug_file")
        
        handlers = {}
        for handler_name in handler_names:
            handlers[handler_name] = self.get_handler_config(handler_name)
        
        # Build formatters configuration
        formatter_names = ["standard", "detailed", "simple"]
        formatters = {}
        for formatter_name in formatter_names:
            formatters[formatter_name] = self.get_formatter_config(formatter_name)
        
        # Build loggers configuration
        loggers = {}
        
        # Root logger
        loggers[""] = {
            "level": self.log_level.value,
            "handlers": ["console", "file", "error_file"] if self.environment == Environment.PRODUCTION else ["console"],
            "propagate": False
        }
        
        # Service-specific loggers
        for service in services:
            loggers[service] = self.get_service_logger_config(service)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": loggers
        }
    
    def log_configuration_summary(self):
        """Log a summary of current logging configuration."""
        print(f"=== Logging Configuration Summary ({self.environment.value}) ===")
        print(f"Log Level: {self.log_level.value}")
        print(f"Log Format: {self.log_format.value}")
        print(f"Log Directory: {self.log_dir}")
        print("=" * 60)


# Global logging settings instance
logging_settings = LoggingSettings()


def get_logging_config() -> Dict[str, Any]:
    """Get complete logging configuration."""
    return logging_settings.get_complete_logging_config()


def get_service_logger_config(service_name: str) -> Dict[str, Any]:
    """Get logger configuration for a specific service."""
    return logging_settings.get_service_logger_config(service_name)


def log_configuration_summary():
    """Log logging configuration summary."""
    logging_settings.log_configuration_summary()


# Initialize on import
if __name__ != "__main__":
    log_configuration_summary()