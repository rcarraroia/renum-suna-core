#!/usr/bin/env python3

"""
Prometheus Setup Validation Script

This script validates that the Prometheus monitoring setup is correctly configured
and all components are working as expected.
"""

import os
import sys
import requests
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class PrometheusValidator:
    """Validator for Prometheus monitoring setup."""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
        self.alertmanager_url = "http://localhost:9093"
        self.prometheus_dir = Path("backend/prometheus")
        
        self.results = []
        self.errors = []
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating Prometheus monitoring setup...\n")
        
        # Configuration file validation
        self.validate_config_files()
        
        # Backend metrics endpoint validation
        self.validate_backend_metrics()
        
        # Service availability validation (if running)
        self.validate_service_availability()
        
        # Configuration syntax validation
        self.validate_configuration_syntax()
        
        # Display results
        self.display_results()
        
        return len(self.errors) == 0
    
    def validate_config_files(self):
        """Validate that all required configuration files exist."""
        print("📁 Validating configuration files...")
        
        required_files = [
            ("prometheus/prometheus.yml", "Prometheus configuration"),
            ("prometheus/alert_rules.yml", "Alert rules"),
            ("prometheus/alertmanager.yml", "Alertmanager configuration"),
            ("prometheus/docker-compose.prometheus.yml", "Docker Compose configuration"),
            ("prometheus/setup_prometheus.py", "Management script"),
            ("prometheus/README.md", "Documentation"),
        ]
        
        for file_path, description in required_files:
            full_path = Path(file_path)
            if full_path.exists():
                self.results.append(f"✅ {description}: Found")
                
                # Check file size (should not be empty)
                if full_path.stat().st_size > 0:
                    self.results.append(f"   ✅ {description}: Not empty")
                else:
                    self.errors.append(f"   ❌ {description}: File is empty")
            else:
                self.errors.append(f"❌ {description}: Not found at {file_path}")
    
    def validate_backend_metrics(self):
        """Validate that the backend metrics endpoint is working."""
        print("🎯 Validating backend metrics endpoint...")
        
        try:
            # Test metrics endpoint
            response = requests.get(f"{self.backend_url}/api/metrics", timeout=10)
            
            if response.status_code == 200:
                self.results.append("✅ Backend metrics endpoint: Accessible")
                
                content = response.text
                
                # Check Prometheus format
                if "# HELP" in content and "# TYPE" in content:
                    self.results.append("✅ Metrics format: Valid Prometheus format")
                    
                    # Count metrics
                    help_lines = [line for line in content.split('\n') if line.startswith('# HELP')]
                    self.results.append(f"✅ Metrics count: {len(help_lines)} metrics available")
                    
                    # Check for expected metrics
                    expected_metrics = [
                        "http_requests_total",
                        "http_request_duration_seconds",
                        "database_queries_total",
                        "redis_operations_total",
                        "worker_tasks_total",
                        "agent_executions_total",
                        "llm_requests_total"
                    ]
                    
                    found_metrics = []
                    for metric in expected_metrics:
                        if metric in content:
                            found_metrics.append(metric)
                    
                    self.results.append(f"✅ Expected metrics: {len(found_metrics)}/{len(expected_metrics)} found")
                    
                    if len(found_metrics) < len(expected_metrics):
                        missing = set(expected_metrics) - set(found_metrics)
                        self.errors.append(f"⚠️  Missing metrics: {', '.join(missing)}")
                
                else:
                    self.errors.append("❌ Metrics format: Not in Prometheus format")
            
            else:
                self.errors.append(f"❌ Backend metrics endpoint: HTTP {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.errors.append("❌ Backend metrics endpoint: Connection refused (backend not running?)")
        except Exception as e:
            self.errors.append(f"❌ Backend metrics endpoint: Error - {e}")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/metrics/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.results.append("✅ Metrics health check: Healthy")
                else:
                    self.errors.append(f"❌ Metrics health check: {data.get('status', 'unknown')}")
            else:
                self.errors.append(f"❌ Metrics health endpoint: HTTP {response.status_code}")
        except Exception as e:
            self.errors.append(f"❌ Metrics health endpoint: Error - {e}")
    
    def validate_service_availability(self):
        """Validate that monitoring services are available (if running)."""
        print("🌐 Validating service availability...")
        
        services = [
            (self.prometheus_url, "Prometheus", "/-/healthy"),
            (self.grafana_url, "Grafana", "/api/health"),
            (self.alertmanager_url, "Alertmanager", "/-/healthy"),
        ]
        
        for base_url, service_name, health_path in services:
            try:
                response = requests.get(f"{base_url}{health_path}", timeout=5)
                if response.status_code == 200:
                    self.results.append(f"✅ {service_name}: Running and healthy")
                else:
                    self.results.append(f"⚠️  {service_name}: Running but unhealthy (HTTP {response.status_code})")
            except requests.exceptions.ConnectionError:
                self.results.append(f"ℹ️  {service_name}: Not running (this is OK if not started yet)")
            except Exception as e:
                self.errors.append(f"❌ {service_name}: Error - {e}")
    
    def validate_configuration_syntax(self):
        """Validate YAML syntax of configuration files."""
        print("🔧 Validating configuration syntax...")
        
        yaml_files = [
            ("prometheus/prometheus.yml", "Prometheus config"),
            ("prometheus/alert_rules.yml", "Alert rules"),
            ("prometheus/alertmanager.yml", "Alertmanager config"),
            ("prometheus/docker-compose.prometheus.yml", "Docker Compose"),
        ]
        
        for file_path, description in yaml_files:
            full_path = Path(file_path)
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        yaml.safe_load(f)
                    self.results.append(f"✅ {description}: Valid YAML syntax")
                except yaml.YAMLError as e:
                    self.errors.append(f"❌ {description}: Invalid YAML - {e}")
                except Exception as e:
                    self.errors.append(f"❌ {description}: Error reading file - {e}")
    
    def validate_prometheus_targets(self):
        """Validate Prometheus targets configuration (if Prometheus is running)."""
        print("🎯 Validating Prometheus targets...")
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                targets = data.get("data", {}).get("activeTargets", [])
                
                self.results.append(f"✅ Prometheus targets: {len(targets)} targets configured")
                
                # Check target health
                healthy_targets = [t for t in targets if t.get("health") == "up"]
                self.results.append(f"✅ Healthy targets: {len(healthy_targets)}/{len(targets)}")
                
                # List targets
                for target in targets:
                    job = target.get("labels", {}).get("job", "unknown")
                    health = target.get("health", "unknown")
                    endpoint = target.get("scrapeUrl", "unknown")
                    
                    if health == "up":
                        self.results.append(f"   ✅ {job}: {health}")
                    else:
                        self.errors.append(f"   ❌ {job}: {health} ({endpoint})")
            
            else:
                self.results.append(f"⚠️  Prometheus targets: Cannot check (HTTP {response.status_code})")
        
        except requests.exceptions.ConnectionError:
            self.results.append("ℹ️  Prometheus targets: Cannot check (Prometheus not running)")
        except Exception as e:
            self.errors.append(f"❌ Prometheus targets: Error - {e}")
    
    def display_results(self):
        """Display validation results."""
        print("\n" + "="*60)
        print("📊 VALIDATION RESULTS")
        print("="*60)
        
        # Display successful checks
        if self.results:
            print("\n✅ PASSED CHECKS:")
            for result in self.results:
                print(f"   {result}")
        
        # Display errors
        if self.errors:
            print(f"\n❌ FAILED CHECKS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        # Summary
        total_checks = len(self.results) + len(self.errors)
        passed_checks = len(self.results)
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total checks: {total_checks}")
        print(f"   Passed: {passed_checks}")
        print(f"   Failed: {len(self.errors)}")
        print(f"   Success rate: {(passed_checks/total_checks*100):.1f}%" if total_checks > 0 else "   Success rate: 0%")
        
        if len(self.errors) == 0:
            print("\n🎉 All validations passed! Prometheus setup is ready.")
        else:
            print(f"\n⚠️  {len(self.errors)} issues found. Please fix them before proceeding.")
        
        print("\n📋 NEXT STEPS:")
        if len(self.errors) == 0:
            print("   1. Start monitoring stack: cd backend/prometheus && python3 setup_prometheus.py start")
            print("   2. Access Prometheus: http://localhost:9090")
            print("   3. Access Grafana: http://localhost:3000 (admin/admin123)")
            print("   4. Configure dashboards and alerts as needed")
        else:
            print("   1. Fix the issues listed above")
            print("   2. Run this validation script again")
            print("   3. Once all checks pass, start the monitoring stack")

def main():
    """Main function."""
    validator = PrometheusValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()