"""
Production-optimized timeout settings for Suna backend.

This module contains environment-specific timeout configurations
optimized for different deployment scenarios.
"""

import os
from typing import Dict, Any
from enum import Enum


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TimeoutSettings:
    """Environment-specific timeout configurations."""
    
    def __init__(self, environment: Environment = None):
        self.environment = environment or self._detect_environment()
        self.settings = self._get_environment_settings()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        if env_name in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env_name in ["stage", "staging"]:
            return Environment.STAGING
        else:
            return Environment.DEVELOPMENT
    
    def _get_environment_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get timeout settings based on environment."""
        
        if self.environment == Environment.PRODUCTION:
            return self._get_production_settings()
        elif self.environment == Environment.STAGING:
            return self._get_staging_settings()
        else:
            return self._get_development_settings()
    
    def _get_development_settings(self) -> Dict[str, Dict[str, Any]]:
        """Development environment settings - more lenient timeouts."""
        return {
            "api": {
                "request_timeout": 300.0,  # 5 minutes for debugging
                "graceful_shutdown": 60.0,
                "keep_alive": 5.0,
                "client_timeout": 120.0,
                "websocket_timeout": 600.0  # 10 minutes
            },
            "database": {
                "connection_timeout": 30.0,
                "query_timeout": 60.0,
                "transaction_timeout": 120.0,
                "pool_timeout": 10.0,
                "idle_timeout": 600.0,
                "max_lifetime": 7200.0
            },
            "redis": {
                "connection_timeout": 10.0,
                "socket_timeout": 30.0,
                "health_check_interval": 60.0,
                "retry_on_timeout": True,
                "socket_keepalive": True
            },
            "http_client": {
                "connect_timeout": 30.0,
                "read_timeout": 60.0,
                "total_timeout": 120.0,
                "pool_timeout": 10.0,
                "max_retries": 5
            },
            "worker": {
                "task_timeout": 600.0,  # 10 minutes
                "shutdown_timeout": 60.0,
                "heartbeat_interval": 120.0,
                "max_retries": 5,
                "retry_delay": 10.0
            },
            "rabbitmq": {
                "connection_timeout": 30.0,
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
                "socket_timeout": 10.0
            }
        }
    
    def _get_staging_settings(self) -> Dict[str, Dict[str, Any]]:
        """Staging environment settings - production-like but slightly more lenient."""
        return {
            "api": {
                "request_timeout": 180.0,  # 3 minutes
                "graceful_shutdown": 45.0,
                "keep_alive": 3.0,
                "client_timeout": 90.0,
                "websocket_timeout": 450.0  # 7.5 minutes
            },
            "database": {
                "connection_timeout": 15.0,
                "query_timeout": 45.0,
                "transaction_timeout": 90.0,
                "pool_timeout": 8.0,
                "idle_timeout": 450.0,
                "max_lifetime": 5400.0
            },
            "redis": {
                "connection_timeout": 8.0,
                "socket_timeout": 20.0,
                "health_check_interval": 45.0,
                "retry_on_timeout": True,
                "socket_keepalive": True
            },
            "http_client": {
                "connect_timeout": 20.0,
                "read_timeout": 45.0,
                "total_timeout": 90.0,
                "pool_timeout": 8.0,
                "max_retries": 4
            },
            "worker": {
                "task_timeout": 450.0,  # 7.5 minutes
                "shutdown_timeout": 45.0,
                "heartbeat_interval": 90.0,
                "max_retries": 4,
                "retry_delay": 8.0
            },
            "rabbitmq": {
                "connection_timeout": 20.0,
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
                "socket_timeout": 8.0
            }
        }
    
    def _get_production_settings(self) -> Dict[str, Dict[str, Any]]:
        """Production environment settings - optimized for performance and reliability."""
        return {
            "api": {
                "request_timeout": 120.0,  # 2 minutes
                "graceful_shutdown": 30.0,
                "keep_alive": 2.0,
                "client_timeout": 60.0,
                "websocket_timeout": 300.0  # 5 minutes
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
            "http_client": {
                "connect_timeout": 10.0,
                "read_timeout": 30.0,
                "total_timeout": 60.0,
                "pool_timeout": 5.0,
                "max_retries": 3
            },
            "worker": {
                "task_timeout": 300.0,  # 5 minutes
                "shutdown_timeout": 30.0,
                "heartbeat_interval": 60.0,
                "max_retries": 3,
                "retry_delay": 5.0
            },
            "rabbitmq": {
                "connection_timeout": 10.0,
                "heartbeat": 600,
                "blocked_connection_timeout": 300,
                "socket_timeout": 5.0
            }
        }
    
    def get_service_config(self, service: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        return self.settings.get(service, {})
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all timeout settings."""
        return self.settings
    
    def validate_settings(self) -> bool:
        """Validate that all timeout settings are reasonable."""
        issues = []
        
        for service, config in self.settings.items():
            # Check for negative values
            for key, value in config.items():
                if isinstance(value, (int, float)) and value < 0:
                    issues.append(f"{service}.{key} has negative value: {value}")
            
            # Service-specific validations
            if service == "api":
                if config.get("graceful_shutdown", 0) > config.get("request_timeout", 0):
                    issues.append(f"{service}: graceful_shutdown should be <= request_timeout")
            
            elif service == "database":
                if config.get("query_timeout", 0) < config.get("connection_timeout", 0):
                    issues.append(f"{service}: query_timeout should be >= connection_timeout")
            
            elif service == "redis":
                if config.get("socket_timeout", 0) < config.get("connection_timeout", 0):
                    issues.append(f"{service}: socket_timeout should be >= connection_timeout")
        
        if issues:
            print(f"Timeout configuration issues found: {issues}")
            return False
        
        return True
    
    def log_settings_summary(self):
        """Log a summary of current timeout settings."""
        print(f"=== Timeout Settings Summary ({self.environment.value}) ===")
        for service, config in self.settings.items():
            print(f"{service.upper()}:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        print("=" * 50)


# Global timeout settings instance
timeout_settings = TimeoutSettings()


def get_timeout_config(service: str) -> Dict[str, Any]:
    """Get timeout configuration for a specific service."""
    return timeout_settings.get_service_config(service)


def get_all_timeout_settings() -> Dict[str, Dict[str, Any]]:
    """Get all timeout settings."""
    return timeout_settings.get_all_settings()


def validate_timeout_configuration() -> bool:
    """Validate timeout configuration."""
    return timeout_settings.validate_settings()


def log_timeout_summary():
    """Log timeout configuration summary."""
    timeout_settings.log_settings_summary()


# Initialize and validate on import
if __name__ != "__main__":
    if not validate_timeout_configuration():
        print("Warning: Timeout configuration validation failed!")