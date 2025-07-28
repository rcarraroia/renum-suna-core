"""
Migration Validator for system updates.

Provides validation and safety checks for:
- Dependency compatibility
- Configuration validity
- Database migration safety
- System health checks
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import importlib.util

logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates system migrations and updates."""
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_python_dependencies(self, requirements_file: str) -> Tuple[bool, List[str]]:
        """Validate Python dependencies for conflicts and compatibility."""
        issues = []
        
        try:
            # Check if requirements file exists
            if not Path(requirements_file).exists():
                issues.append(f"Requirements file not found: {requirements_file}")
                return False, issues
            
            # Try to resolve dependencies
            result = subprocess.run([
                "python", "-m", "pip", "check"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                issues.append(f"Dependency conflicts detected: {result.stdout}")
            
            # Check for deprecated packages
            with open(requirements_file, 'r') as f:
                content = f.read()
                
            deprecated_packages = ['aioredis']
            for pkg in deprecated_packages:
                if pkg in content:
                    issues.append(f"Deprecated package found: {pkg}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate dependencies: {e}")
            return False, issues
    
    def validate_redis_config(self, config_file: str) -> Tuple[bool, List[str]]:
        """Validate Redis configuration file."""
        issues = []
        
        try:
            if not Path(config_file).exists():
                issues.append(f"Redis config file not found: {config_file}")
                return False, issues
            
            with open(config_file, 'r') as f:
                config_content = f.read()
            
            # Check for required settings
            required_settings = [
                'maxmemory',
                'maxmemory-policy', 
                'timeout'
            ]
            
            for setting in required_settings:
                if setting not in config_content:
                    issues.append(f"Missing Redis setting: {setting}")
            
            # Check for security settings
            if 'requirepass' not in config_content:
                issues.append("Redis password not configured (security risk)")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate Redis config: {e}")
            return False, issues
    
    def validate_docker_compose(self, compose_file: str = "docker-compose.yaml") -> Tuple[bool, List[str]]:
        """Validate Docker Compose configuration."""
        issues = []
        
        try:
            if not Path(compose_file).exists():
                issues.append(f"Docker Compose file not found: {compose_file}")
                return False, issues
            
            # Validate compose file syntax
            result = subprocess.run([
                "docker", "compose", "-f", compose_file, "config"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                issues.append(f"Docker Compose syntax error: {result.stderr}")
            
            # Check for resource limits
            with open(compose_file, 'r') as f:
                content = f.read()
            
            if 'deploy:' not in content or 'resources:' not in content:
                issues.append("Missing resource limits in Docker Compose")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate Docker Compose: {e}")
            return False, issues
    
    async def validate_service_connectivity(self) -> Tuple[bool, List[str]]:
        """Validate connectivity to external services."""
        issues = []
        
        try:
            # Test Redis connectivity
            try:
                import redis.asyncio as redis
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                await redis_client.ping()
                await redis_client.close()
            except Exception as e:
                issues.append(f"Redis connectivity failed: {e}")
            
            # Test database connectivity (if configured)
            try:
                # This would test Supabase connection
                # Implementation depends on current setup
                pass
            except Exception as e:
                issues.append(f"Database connectivity failed: {e}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate service connectivity: {e}")
            return False, issues
    
    def validate_environment_variables(self, env_file: str) -> Tuple[bool, List[str]]:
        """Validate environment variables configuration."""
        issues = []
        
        try:
            if not Path(env_file).exists():
                issues.append(f"Environment file not found: {env_file}")
                return False, issues
            
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Check for required environment variables
            required_vars = [
                'REDIS_HOST',
                'REDIS_PORT',
                'SUPABASE_URL',
                'SUPABASE_ANON_KEY'
            ]
            
            for var in required_vars:
                if var not in content:
                    issues.append(f"Missing environment variable: {var}")
            
            # Check for sensitive data exposure
            if 'password' in content.lower() and '=' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'password' in line.lower() and '=' in line:
                        if line.split('=')[1].strip() == '':
                            issues.append("Empty password detected")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate environment variables: {e}")
            return False, issues
    
    def validate_database_migration_safety(self, migration_scripts: List[str]) -> Tuple[bool, List[str]]:
        """Validate database migration scripts for safety."""
        issues = []
        
        try:
            for script in migration_scripts:
                if not Path(script).exists():
                    issues.append(f"Migration script not found: {script}")
                    continue
                
                with open(script, 'r') as f:
                    sql_content = f.read().upper()
                
                # Check for dangerous operations
                dangerous_operations = [
                    'DROP TABLE',
                    'DROP DATABASE', 
                    'TRUNCATE',
                    'DELETE FROM'
                ]
                
                for operation in dangerous_operations:
                    if operation in sql_content:
                        issues.append(f"Dangerous operation in {script}: {operation}")
                
                # Check for rollback availability
                if 'ALTER TABLE' in sql_content:
                    rollback_script = script.replace('.sql', '_rollback.sql')
                    if not Path(rollback_script).exists():
                        issues.append(f"Missing rollback script for: {script}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to validate migration scripts: {e}")
            return False, issues
    
    def run_comprehensive_validation(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Run all validation checks and return comprehensive results."""
        results = {}
        
        # Validate Python dependencies
        results['dependencies'] = self.validate_python_dependencies('backend/pyproject.toml')
        results['renum_dependencies'] = self.validate_python_dependencies('renum-backend/requirements.txt')
        
        # Validate configurations
        results['redis_config'] = self.validate_redis_config('backend/services/docker/redis.conf')
        results['docker_compose'] = self.validate_docker_compose()
        
        # Validate environment files
        results['backend_env'] = self.validate_environment_variables('backend/.env')
        results['frontend_env'] = self.validate_environment_variables('frontend/.env.local')
        
        self.validation_results = results
        return results
    
    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report."""
        if not self.validation_results:
            return "No validation results available. Run comprehensive validation first."
        
        report = ["=== MIGRATION VALIDATION REPORT ===\n"]
        
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for result in self.validation_results.values() if result[0])
        
        report.append(f"Overall Status: {passed_checks}/{total_checks} checks passed\n")
        
        for check_name, (passed, issues) in self.validation_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{status} {check_name.replace('_', ' ').title()}")
            
            if issues:
                for issue in issues:
                    report.append(f"  - {issue}")
            report.append("")
        
        return "\n".join(report)