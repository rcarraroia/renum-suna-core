"""
Configuration Manager for system settings.

Manages configuration files including:
- Redis configuration
- Docker Compose settings
- Environment variables
- Application configurations
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from configparser import ConfigParser

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages system configuration files and settings."""
    
    def __init__(self):
        self.config_templates = {
            'redis': {
                'maxmemory': '2gb',
                'maxmemory-policy': 'allkeys-lru',
                'appendonly': 'yes',
                'appendfsync': 'everysec',
                'timeout': '120',
                'loglevel': 'warning',
                'requirepass': 'secure_redis_password'
            },
            'docker_resources': {
                'deploy': {
                    'resources': {
                        'limits': {
                            'cpus': '2.0',
                            'memory': '4G'
                        },
                        'reservations': {
                            'cpus': '1.0',
                            'memory': '2G'
                        }
                    }
                }
            }
        }
    
    def read_redis_config(self, config_file: str) -> Dict[str, str]:
        """Read Redis configuration file."""
        config = {}
        
        try:
            if not Path(config_file).exists():
                logger.warning(f"Redis config file not found: {config_file}")
                return config
            
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ' ' in line:
                            key, value = line.split(' ', 1)
                            config[key] = value
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to read Redis config: {e}")
            return {}
    
    def write_redis_config(self, config_file: str, config: Dict[str, str]) -> bool:
        """Write Redis configuration file."""
        try:
            # Ensure directory exists
            Path(config_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                f.write("# Redis Configuration for Production\n")
                f.write("# Generated by Suna Migration Utils\n\n")
                
                for key, value in config.items():
                    f.write(f"{key} {value}\n")
            
            logger.info(f"Redis configuration written to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Redis config: {e}")
            return False
    
    def update_redis_config(self, config_file: str, updates: Dict[str, str]) -> bool:
        """Update Redis configuration with new settings."""
        try:
            current_config = self.read_redis_config(config_file)
            current_config.update(updates)
            return self.write_redis_config(config_file, current_config)
            
        except Exception as e:
            logger.error(f"Failed to update Redis config: {e}")
            return False
    
    def read_docker_compose(self, compose_file: str) -> Dict:
        """Read Docker Compose configuration."""
        try:
            if not Path(compose_file).exists():
                logger.warning(f"Docker Compose file not found: {compose_file}")
                return {}
            
            with open(compose_file, 'r') as f:
                return yaml.safe_load(f)
            
        except Exception as e:
            logger.error(f"Failed to read Docker Compose: {e}")
            return {}
    
    def write_docker_compose(self, compose_file: str, config: Dict) -> bool:
        """Write Docker Compose configuration."""
        try:
            with open(compose_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Docker Compose configuration written to: {compose_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Docker Compose: {e}")
            return False
    
    def add_resource_limits(self, compose_file: str, service_name: str, limits: Dict) -> bool:
        """Add resource limits to a Docker Compose service."""
        try:
            config = self.read_docker_compose(compose_file)
            
            if 'services' not in config:
                config['services'] = {}
            
            if service_name not in config['services']:
                logger.warning(f"Service not found: {service_name}")
                return False
            
            config['services'][service_name]['deploy'] = limits
            
            return self.write_docker_compose(compose_file, config)
            
        except Exception as e:
            logger.error(f"Failed to add resource limits: {e}")
            return False
    
    def read_env_file(self, env_file: str) -> Dict[str, str]:
        """Read environment variables from .env file."""
        env_vars = {}
        
        try:
            if not Path(env_file).exists():
                logger.warning(f"Environment file not found: {env_file}")
                return env_vars
            
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            return env_vars
            
        except Exception as e:
            logger.error(f"Failed to read environment file: {e}")
            return {}
    
    def write_env_file(self, env_file: str, env_vars: Dict[str, str]) -> bool:
        """Write environment variables to .env file."""
        try:
            # Ensure directory exists
            Path(env_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(env_file, 'w') as f:
                f.write("# Environment Configuration\n")
                f.write("# Generated by Suna Migration Utils\n\n")
                
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Environment configuration written to: {env_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write environment file: {e}")
            return False
    
    def update_env_file(self, env_file: str, updates: Dict[str, str]) -> bool:
        """Update environment file with new variables."""
        try:
            current_env = self.read_env_file(env_file)
            current_env.update(updates)
            return self.write_env_file(env_file, current_env)
            
        except Exception as e:
            logger.error(f"Failed to update environment file: {e}")
            return False
    
    def create_production_redis_config(self, config_file: str) -> bool:
        """Create production-ready Redis configuration."""
        return self.write_redis_config(config_file, self.config_templates['redis'])
    
    def add_docker_resource_limits(self, compose_file: str) -> bool:
        """Add resource limits to all services in Docker Compose."""
        try:
            config = self.read_docker_compose(compose_file)
            
            if 'services' not in config:
                logger.error("No services found in Docker Compose")
                return False
            
            # Add resource limits to main services
            main_services = ['backend', 'worker', 'frontend']
            
            for service_name in main_services:
                if service_name in config['services']:
                    config['services'][service_name].update(
                        self.config_templates['docker_resources']
                    )
            
            return self.write_docker_compose(compose_file, config)
            
        except Exception as e:
            logger.error(f"Failed to add Docker resource limits: {e}")
            return False
    
    def validate_configuration(self, config_type: str, config_file: str) -> Tuple[bool, List[str]]:
        """Validate configuration file."""
        issues = []
        
        try:
            if config_type == 'redis':
                config = self.read_redis_config(config_file)
                required_settings = ['maxmemory', 'maxmemory-policy', 'timeout']
                
                for setting in required_settings:
                    if setting not in config:
                        issues.append(f"Missing Redis setting: {setting}")
                
                if 'requirepass' not in config:
                    issues.append("Redis password not configured")
            
            elif config_type == 'docker':
                config = self.read_docker_compose(config_file)
                
                if 'services' not in config:
                    issues.append("No services defined in Docker Compose")
                else:
                    for service_name, service_config in config['services'].items():
                        if 'deploy' not in service_config:
                            issues.append(f"No resource limits for service: {service_name}")
            
            elif config_type == 'env':
                env_vars = self.read_env_file(config_file)
                required_vars = ['REDIS_HOST', 'REDIS_PORT']
                
                for var in required_vars:
                    if var not in env_vars:
                        issues.append(f"Missing environment variable: {var}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Configuration validation failed: {e}")
            return False, issues
    
    def create_configuration_summary(self) -> Dict[str, Any]:
        """Create a summary of all configuration files."""
        summary = {
            "redis_config": {},
            "docker_config": {},
            "env_files": {},
            "validation_status": {}
        }
        
        # Check Redis configuration
        redis_config_file = "backend/services/docker/redis.conf"
        if Path(redis_config_file).exists():
            summary["redis_config"] = self.read_redis_config(redis_config_file)
            valid, issues = self.validate_configuration('redis', redis_config_file)
            summary["validation_status"]["redis"] = {"valid": valid, "issues": issues}
        
        # Check Docker Compose
        compose_file = "docker-compose.yaml"
        if Path(compose_file).exists():
            summary["docker_config"] = self.read_docker_compose(compose_file)
            valid, issues = self.validate_configuration('docker', compose_file)
            summary["validation_status"]["docker"] = {"valid": valid, "issues": issues}
        
        # Check environment files
        env_files = ["backend/.env", "frontend/.env.local"]
        for env_file in env_files:
            if Path(env_file).exists():
                summary["env_files"][env_file] = self.read_env_file(env_file)
                valid, issues = self.validate_configuration('env', env_file)
                summary["validation_status"][env_file] = {"valid": valid, "issues": issues}
        
        return summary