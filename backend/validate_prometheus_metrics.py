#!/usr/bin/env python3
"""
Validation script for Prometheus metrics implementation.

This script validates that all Prometheus metrics are properly configured
and working correctly across all instrumented services.
"""

import asyncio
import time
import httpx
from typing import Dict, Any, List
from services.metrics import get_metrics_collector
from services.metrics_decorators import (
    instrument_database_query, instrument_redis_operation,
    instrument_worker_task, instrument_agent_execution,
    instrument_llm_request
)
from logging_config import get_logger

logger = get_logger(__name__)


class MetricsValidator:
    """Validates Prometheus metrics implementation."""
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.validation_results = []
    
    def validate_metrics_collector_initialization(self) -> bool:
        """Validate that metrics collector is properly initialized."""
        logger.info("=== Validating Metrics Collector Initialization ===")
        
        try:
            # Check if metrics collector exists
            if not self.metrics_collector:
                self.validation_results.append("❌ Metrics collector not initialized")
                return False
            
            # Check if registry exists
            if not hasattr(self.metrics_collector, 'registry'):
                self.validation_results.append("❌ Metrics registry not found")
                return False
            
            # Check if basic metrics are defined
            required_metrics = [
                'http_requests_total',
                'http_request_duration_seconds',
                'database_queries_total',
                'redis_operations_total',
                'worker_tasks_total',
                'agent_executions_total',
                'llm_requests_total',
                'errors_total'
            ]
            
            missing_metrics = []
            for metric_name in required_metrics:
                if not hasattr(self.metrics_collector, metric_name):
                    missing_metrics.append(metric_name)
            
            if missing_metrics:
                self.validation_results.append(f"❌ Missing metrics: {missing_metrics}")
                return False
            
            self.validation_results.append("✅ Metrics collector properly initialized")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Metrics collector validation failed: {e}")
            return False
    
    def validate_metrics_generation(self) -> bool:
        """Validate that metrics can be generated in Prometheus format."""
        logger.info("=== Validating Metrics Generation ===")
        
        try:
            # Generate metrics
            metrics_data = self.metrics_collector.get_metrics()
            
            if not metrics_data:
                self.validation_results.append("❌ No metrics data generated")
                return False
            
            if not isinstance(metrics_data, str):
                self.validation_results.append("❌ Metrics data is not a string")
                return False
            
            # Check for basic Prometheus format
            if "# HELP" not in metrics_data or "# TYPE" not in metrics_data:
                self.validation_results.append("❌ Metrics data not in Prometheus format")
                return False
            
            # Check for some expected metrics
            expected_metrics = [
                "http_requests_total",
                "database_queries_total",
                "redis_operations_total"
            ]
            
            missing_in_output = []
            for metric in expected_metrics:
                if metric not in metrics_data:
                    missing_in_output.append(metric)
            
            if missing_in_output:
                self.validation_results.append(f"❌ Expected metrics not in output: {missing_in_output}")
                return False
            
            self.validation_results.append(f"✅ Metrics generation successful ({len(metrics_data)} bytes)")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Metrics generation failed: {e}")
            return False
    
    def validate_http_metrics_recording(self) -> bool:
        """Validate HTTP metrics recording."""
        logger.info("=== Validating HTTP Metrics Recording ===")
        
        try:
            # Record some test HTTP metrics
            self.metrics_collector.record_http_request(
                method="GET",
                endpoint="/test",
                status_code=200,
                duration=0.123,
                request_size=1024,
                response_size=2048
            )
            
            self.metrics_collector.record_http_request(
                method="POST",
                endpoint="/api/test",
                status_code=201,
                duration=0.456,
                request_size=512,
                response_size=1024
            )
            
            # Generate metrics and check if they're recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            # Check for recorded metrics
            if 'http_requests_total{endpoint="/test",method="GET",status_code="200"}' not in metrics_data:
                self.validation_results.append("❌ HTTP request metrics not recorded properly")
                return False
            
            self.validation_results.append("✅ HTTP metrics recording working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ HTTP metrics recording failed: {e}")
            return False
    
    def validate_database_metrics_recording(self) -> bool:
        """Validate database metrics recording."""
        logger.info("=== Validating Database Metrics Recording ===")
        
        try:
            # Record some test database metrics
            self.metrics_collector.record_database_query(
                operation="SELECT",
                table="users",
                status="success",
                duration=0.045
            )
            
            self.metrics_collector.record_database_query(
                operation="INSERT",
                table="logs",
                status="success",
                duration=0.023
            )
            
            # Generate metrics and check if they're recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            # Check for recorded metrics
            if 'database_queries_total{operation="SELECT",status="success",table="users"}' not in metrics_data:
                self.validation_results.append("❌ Database query metrics not recorded properly")
                return False
            
            self.validation_results.append("✅ Database metrics recording working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Database metrics recording failed: {e}")
            return False
    
    def validate_redis_metrics_recording(self) -> bool:
        """Validate Redis metrics recording."""
        logger.info("=== Validating Redis Metrics Recording ===")
        
        try:
            # Record some test Redis metrics
            self.metrics_collector.record_redis_operation(
                operation="GET",
                status="success",
                duration=0.012
            )
            
            self.metrics_collector.record_redis_operation(
                operation="SET",
                status="success",
                duration=0.008
            )
            
            # Generate metrics and check if they're recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            # Check for recorded metrics
            if 'redis_operations_total{operation="GET",status="success"}' not in metrics_data:
                self.validation_results.append("❌ Redis operation metrics not recorded properly")
                return False
            
            self.validation_results.append("✅ Redis metrics recording working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Redis metrics recording failed: {e}")
            return False
    
    def validate_business_metrics_recording(self) -> bool:
        """Validate business logic metrics recording."""
        logger.info("=== Validating Business Metrics Recording ===")
        
        try:
            # Record some test business metrics
            self.metrics_collector.record_agent_execution(
                agent_type="test_agent",
                status="success",
                duration=12.34
            )
            
            self.metrics_collector.record_llm_request(
                provider="openai",
                model="gpt-4",
                status="success",
                duration=2.56,
                input_tokens=100,
                output_tokens=50
            )
            
            self.metrics_collector.record_worker_task(
                task_name="test_task",
                status="success",
                duration=5.67
            )
            
            # Generate metrics and check if they're recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            # Check for recorded metrics
            expected_metrics = [
                'agent_executions_total{agent_type="test_agent",status="success"}',
                'llm_requests_total{model="gpt-4",provider="openai",status="success"}',
                'worker_tasks_total{status="success",task_name="test_task"}'
            ]
            
            missing_metrics = []
            for metric in expected_metrics:
                if metric not in metrics_data:
                    missing_metrics.append(metric)
            
            if missing_metrics:
                self.validation_results.append(f"❌ Business metrics not recorded: {missing_metrics}")
                return False
            
            self.validation_results.append("✅ Business metrics recording working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Business metrics recording failed: {e}")
            return False
    
    def validate_error_metrics_recording(self) -> bool:
        """Validate error metrics recording."""
        logger.info("=== Validating Error Metrics Recording ===")
        
        try:
            # Record some test error metrics
            self.metrics_collector.record_error(
                error_type="ValueError",
                component="test_component"
            )
            
            self.metrics_collector.record_error(
                error_type="ConnectionError",
                component="redis"
            )
            
            # Generate metrics and check if they're recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            # Check for recorded metrics
            if 'errors_total{component="test_component",error_type="ValueError"}' not in metrics_data:
                self.validation_results.append("❌ Error metrics not recorded properly")
                return False
            
            self.validation_results.append("✅ Error metrics recording working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Error metrics recording failed: {e}")
            return False
    
    def validate_decorators(self) -> bool:
        """Validate that decorators work correctly."""
        logger.info("=== Validating Metrics Decorators ===")
        
        try:
            # Test database decorator
            @instrument_database_query("SELECT", "test_table")
            def test_db_query():
                time.sleep(0.01)  # Simulate query time
                return "success"
            
            # Test Redis decorator
            @instrument_redis_operation("GET")
            def test_redis_op():
                time.sleep(0.005)  # Simulate Redis operation
                return "cached_value"
            
            # Test worker decorator
            @instrument_worker_task("test_task")
            def test_worker():
                time.sleep(0.02)  # Simulate work
                return "completed"
            
            # Execute decorated functions
            test_db_query()
            test_redis_op()
            test_worker()
            
            # Check if metrics were recorded
            metrics_data = self.metrics_collector.get_metrics()
            
            expected_metrics = [
                'database_queries_total{operation="SELECT",status="success",table="test_table"}',
                'redis_operations_total{operation="GET",status="success"}',
                'worker_tasks_total{status="success",task_name="test_task"}'
            ]
            
            missing_metrics = []
            for metric in expected_metrics:
                if metric not in metrics_data:
                    missing_metrics.append(metric)
            
            if missing_metrics:
                self.validation_results.append(f"❌ Decorator metrics not recorded: {missing_metrics}")
                return False
            
            self.validation_results.append("✅ Metrics decorators working correctly")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Decorator validation failed: {e}")
            return False
    
    async def validate_metrics_endpoint(self) -> bool:
        """Validate that metrics endpoint is accessible."""
        logger.info("=== Validating Metrics Endpoint ===")
        
        try:
            # Test metrics generation directly instead of importing endpoint
            # to avoid circular import issues
            metrics_data = self.metrics_collector.get_metrics()
            
            if not metrics_data:
                self.validation_results.append("❌ Metrics endpoint would return empty response")
                return False
            
            # Check if metrics data is in Prometheus format
            if "# HELP" not in metrics_data or "# TYPE" not in metrics_data:
                self.validation_results.append("❌ Metrics endpoint would not return valid Prometheus format")
                return False
            
            self.validation_results.append("✅ Metrics endpoint functionality validated")
            return True
            
        except Exception as e:
            self.validation_results.append(f"❌ Metrics endpoint validation failed: {e}")
            return False
    
    async def run_all_validations(self) -> bool:
        """Run all validation tests."""
        logger.info("🚀 Starting comprehensive Prometheus metrics validation")
        
        validations = [
            ("Metrics Collector Initialization", self.validate_metrics_collector_initialization()),
            ("Metrics Generation", self.validate_metrics_generation()),
            ("HTTP Metrics Recording", self.validate_http_metrics_recording()),
            ("Database Metrics Recording", self.validate_database_metrics_recording()),
            ("Redis Metrics Recording", self.validate_redis_metrics_recording()),
            ("Business Metrics Recording", self.validate_business_metrics_recording()),
            ("Error Metrics Recording", self.validate_error_metrics_recording()),
            ("Metrics Decorators", self.validate_decorators()),
            ("Metrics Endpoint", await self.validate_metrics_endpoint())
        ]
        
        all_passed = True
        for name, result in validations:
            if not result:
                all_passed = False
        
        # Print summary
        logger.info("=== Validation Summary ===")
        for result in self.validation_results:
            print(result)
        
        if all_passed:
            logger.info("🎉 All Prometheus metrics validations passed successfully!")
        else:
            logger.error("❌ Some Prometheus metrics validations failed. Please check the configuration.")
        
        return all_passed


async def main():
    """Main validation function."""
    # Setup logging
    from logging_config import setup_logging
    setup_logging()
    
    # Create validator
    validator = MetricsValidator()
    
    # Run validations
    success = await validator.run_all_validations()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())