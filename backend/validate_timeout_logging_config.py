#!/usr/bin/env python3
"""
Validation script for timeout and logging configurations.

This script validates that all timeout and logging configurations
are properly set up and working correctly across all services.
"""

import asyncio
import logging
import sys
import time
from typing import Dict, Any, List
import redis.asyncio as redis
import httpx
from logging_config import setup_logging, get_logger, get_timeout_config
from services.timeout_config import TimeoutManager, validate_timeout_configuration
from middleware.timeout_middleware import TimeoutMiddleware


class ConfigurationValidator:
    """Validates timeout and logging configurations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.timeout_manager = TimeoutManager()
        self.validation_results = []
    
    def validate_logging_setup(self) -> bool:
        """Validate logging configuration."""
        self.logger.info("=== Validating Logging Configuration ===")
        
        try:
            # Test different log levels
            test_logger = get_logger("test_logger")
            test_logger.debug("Debug message test")
            test_logger.info("Info message test")
            test_logger.warning("Warning message test")
            test_logger.error("Error message test")
            
            # Test structured logging with extra fields
            test_logger.info("Structured logging test", extra={
                "user_id": "test_user",
                "request_id": "test_request",
                "execution_time": 0.123
            })
            
            self.validation_results.append("✅ Logging configuration is working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Logging configuration failed: {e}")
            return False
    
    def validate_timeout_configurations(self) -> bool:
        """Validate timeout configurations for all services."""
        self.logger.info("=== Validating Timeout Configurations ===")
        
        try:
            # Validate timeout configuration consistency
            if not validate_timeout_configuration():
                self.validation_results.append("❌ Timeout configuration validation failed")
                return False
            
            # Test each service configuration
            services = ["redis", "database", "http_client", "worker", "rabbitmq", "api"]
            for service in services:
                config = get_timeout_config(service)
                if not config:
                    self.validation_results.append(f"❌ No timeout configuration found for {service}")
                    return False
                
                self.logger.info(f"Timeout config for {service}", extra={
                    "service": service,
                    "config": config
                })
            
            self.validation_results.append("✅ All timeout configurations are valid")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Timeout configuration validation failed: {e}")
            return False
    
    async def validate_redis_connection(self) -> bool:
        """Validate Redis connection with timeout settings."""
        self.logger.info("=== Validating Redis Connection ===")
        
        try:
            redis_config = self.timeout_manager.get_redis_config()
            
            # Create Redis client with timeout configuration
            redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True,
                **redis_config
            )
            
            # Test connection
            start_time = time.time()
            await redis_client.ping()
            connection_time = time.time() - start_time
            
            # Test basic operations
            await redis_client.set("test_key", "test_value", ex=60)
            value = await redis_client.get("test_key")
            await redis_client.delete("test_key")
            
            await redis_client.close()
            
            self.validation_results.append(f"✅ Redis connection successful (took {connection_time:.3f}s)")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Redis connection failed: {e}")
            return False
    
    async def validate_http_client_timeouts(self) -> bool:
        """Validate HTTP client timeout configuration."""
        self.logger.info("=== Validating HTTP Client Timeouts ===")
        
        try:
            http_config = self.timeout_manager.get_http_client_config()
            
            # Extract timeout and limits separately
            timeout_config = http_config.get("timeout", {})
            limits_config = http_config.get("limits", {})
            
            # Create HTTP client with timeout configuration
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(**timeout_config),
                limits=httpx.Limits(**limits_config)
            ) as client:
                # Test a quick request
                start_time = time.time()
                response = await client.get("https://httpbin.org/delay/1")
                request_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.validation_results.append(f"✅ HTTP client working correctly (took {request_time:.3f}s)")
                    return True
                else:
                    self.validation_results.append(f"❌ HTTP client returned status {response.status_code}")
                    return False
            
        except Exception as e:
            self.validation_results.append(f"❌ HTTP client validation failed: {e}")
            return False
    
    def validate_middleware_setup(self) -> bool:
        """Validate timeout middleware configuration."""
        self.logger.info("=== Validating Middleware Setup ===")
        
        try:
            # Test middleware initialization
            from fastapi import FastAPI
            from middleware.timeout_middleware import setup_timeout_middleware
            app = FastAPI()
            
            # Setup timeout middleware
            app = setup_timeout_middleware(app)
            
            self.validation_results.append("✅ Timeout middleware setup successful")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Middleware setup failed: {e}")
            return False
    
    def validate_gunicorn_configuration(self) -> bool:
        """Validate Gunicorn configuration."""
        self.logger.info("=== Validating Gunicorn Configuration ===")
        
        try:
            # Check if gunicorn.conf.py exists and can be imported
            import os
            if not os.path.exists("gunicorn.conf.py"):
                self.validation_results.append("❌ gunicorn.conf.py file not found")
                return False
            
            # Check if timeout values are reasonable
            api_timeouts = get_timeout_config("api")
            timeout = api_timeouts.get("request_timeout", 120)
            graceful_timeout = api_timeouts.get("graceful_shutdown", 30)
            
            if timeout > 0 and graceful_timeout > 0 and graceful_timeout <= timeout:
                self.validation_results.append("✅ Gunicorn configuration is valid")
                return True
            else:
                self.validation_results.append("❌ Gunicorn timeout configuration is invalid")
                return False
            
        except Exception as e:
            self.validation_results.append(f"❌ Gunicorn configuration validation failed: {e}")
            return False
    
    def validate_docker_configurations(self) -> bool:
        """Validate Docker service configurations."""
        self.logger.info("=== Validating Docker Configurations ===")
        
        try:
            # Check if configuration files exist
            import os
            
            config_files = [
                "services/docker/redis.conf",
                "services/docker/rabbitmq.conf",
                "../docker-compose.yaml"
            ]
            
            missing_files = []
            for config_file in config_files:
                if not os.path.exists(config_file):
                    missing_files.append(config_file)
            
            if missing_files:
                self.validation_results.append(f"❌ Missing configuration files: {missing_files}")
                return False
            
            self.validation_results.append("✅ All Docker configuration files exist")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Docker configuration validation failed: {e}")
            return False
    
    async def run_all_validations(self) -> bool:
        """Run all validation tests."""
        self.logger.info("🚀 Starting comprehensive timeout and logging validation")
        
        validations = [
            ("Logging Setup", self.validate_logging_setup()),
            ("Timeout Configurations", self.validate_timeout_configurations()),
            ("Redis Connection", await self.validate_redis_connection()),
            ("HTTP Client Timeouts", await self.validate_http_client_timeouts()),
            ("Middleware Setup", self.validate_middleware_setup()),
            ("Gunicorn Configuration", self.validate_gunicorn_configuration()),
            ("Docker Configurations", self.validate_docker_configurations())
        ]
        
        all_passed = True
        for name, result in validations:
            if not result:
                all_passed = False
        
        # Print summary
        self.logger.info("=== Validation Summary ===")
        for result in self.validation_results:
            print(result)
        
        if all_passed:
            self.logger.info("🎉 All validations passed successfully!")
        else:
            self.logger.error("❌ Some validations failed. Please check the configuration.")
        
        return all_passed


async def main():
    """Main validation function."""
    # Setup logging
    setup_logging()
    
    # Create validator
    validator = ConfigurationValidator()
    
    # Run validations
    success = await validator.run_all_validations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())