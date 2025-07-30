#!/usr/bin/env python3

"""
Prometheus Setup and Management Script

This script helps set up and manage Prometheus monitoring for the Suna/Renum backend.
It provides utilities for starting, stopping, and configuring the monitoring stack.
"""

import os
import sys
import subprocess
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional

class PrometheusManager:
    """Manager class for Prometheus monitoring stack."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.compose_file = self.base_path / "docker-compose.prometheus.yml"
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
        self.alertmanager_url = "http://localhost:9093"
        
    def start_monitoring_stack(self, services: List[str] = None) -> bool:
        """Start the Prometheus monitoring stack."""
        print("🚀 Starting Prometheus monitoring stack...")
        
        try:
            cmd = ["docker-compose", "-f", str(self.compose_file), "up", "-d"]
            if services:
                cmd.extend(services)
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode == 0:
                print("✅ Monitoring stack started successfully!")
                self._wait_for_services()
                self._display_service_urls()
                return True
            else:
                print(f"❌ Failed to start monitoring stack: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting monitoring stack: {e}")
            return False
    
    def stop_monitoring_stack(self) -> bool:
        """Stop the Prometheus monitoring stack."""
        print("🛑 Stopping Prometheus monitoring stack...")
        
        try:
            cmd = ["docker-compose", "-f", str(self.compose_file), "down"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode == 0:
                print("✅ Monitoring stack stopped successfully!")
                return True
            else:
                print(f"❌ Failed to stop monitoring stack: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error stopping monitoring stack: {e}")
            return False
    
    def restart_monitoring_stack(self) -> bool:
        """Restart the Prometheus monitoring stack."""
        print("🔄 Restarting Prometheus monitoring stack...")
        return self.stop_monitoring_stack() and self.start_monitoring_stack()
    
    def check_service_health(self) -> Dict[str, bool]:
        """Check the health of all monitoring services."""
        print("🔍 Checking service health...")
        
        health_status = {}
        
        # Check Prometheus
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            health_status["prometheus"] = response.status_code == 200
        except:
            health_status["prometheus"] = False
        
        # Check Grafana
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            health_status["grafana"] = response.status_code == 200
        except:
            health_status["grafana"] = False
        
        # Check Alertmanager
        try:
            response = requests.get(f"{self.alertmanager_url}/-/healthy", timeout=5)
            health_status["alertmanager"] = response.status_code == 200
        except:
            health_status["alertmanager"] = False
        
        # Display results
        for service, is_healthy in health_status.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"   {service}: {status}")
        
        return health_status
    
    def validate_configuration(self) -> bool:
        """Validate Prometheus configuration files."""
        print("🔧 Validating Prometheus configuration...")
        
        config_files = [
            ("prometheus.yml", "Prometheus config"),
            ("alert_rules.yml", "Alert rules"),
            ("alertmanager.yml", "Alertmanager config"),
        ]
        
        all_valid = True
        
        for filename, description in config_files:
            file_path = self.base_path / filename
            if file_path.exists():
                print(f"   ✅ {description}: Found")
                
                # Basic YAML validation
                try:
                    import yaml
                    with open(file_path, 'r') as f:
                        yaml.safe_load(f)
                    print(f"   ✅ {description}: Valid YAML")
                except Exception as e:
                    print(f"   ❌ {description}: Invalid YAML - {e}")
                    all_valid = False
            else:
                print(f"   ❌ {description}: Not found")
                all_valid = False
        
        return all_valid
    
    def test_metrics_endpoint(self, backend_url: str = "http://localhost:8000") -> bool:
        """Test if the backend metrics endpoint is accessible."""
        print("🧪 Testing backend metrics endpoint...")
        
        try:
            response = requests.get(f"{backend_url}/api/metrics", timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Metrics endpoint is accessible")
                
                # Check if it's Prometheus format
                content = response.text
                if "# HELP" in content and "# TYPE" in content:
                    print("   ✅ Metrics are in Prometheus format")
                    
                    # Count metrics
                    metric_lines = [line for line in content.split('\n') if line and not line.startswith('#')]
                    print(f"   📊 Found {len(metric_lines)} metric data points")
                    
                    return True
                else:
                    print("   ❌ Metrics are not in Prometheus format")
                    return False
            else:
                print(f"   ❌ Metrics endpoint returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Failed to access metrics endpoint: {e}")
            return False
    
    def reload_prometheus_config(self) -> bool:
        """Reload Prometheus configuration without restart."""
        print("🔄 Reloading Prometheus configuration...")
        
        try:
            response = requests.post(f"{self.prometheus_url}/-/reload", timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Prometheus configuration reloaded successfully")
                return True
            else:
                print(f"   ❌ Failed to reload configuration: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error reloading configuration: {e}")
            return False
    
    def get_prometheus_targets(self) -> Dict:
        """Get current Prometheus targets and their status."""
        print("🎯 Checking Prometheus targets...")
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                targets = data.get("data", {}).get("activeTargets", [])
                
                print(f"   📊 Found {len(targets)} targets")
                
                for target in targets:
                    job = target.get("labels", {}).get("job", "unknown")
                    health = target.get("health", "unknown")
                    endpoint = target.get("scrapeUrl", "unknown")
                    
                    status_icon = "✅" if health == "up" else "❌"
                    print(f"   {status_icon} {job}: {health} ({endpoint})")
                
                return data
            else:
                print(f"   ❌ Failed to get targets: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"   ❌ Error getting targets: {e}")
            return {}
    
    def _wait_for_services(self, timeout: int = 60):
        """Wait for services to become healthy."""
        print("⏳ Waiting for services to start...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            health = self.check_service_health()
            if all(health.values()):
                print("✅ All services are healthy!")
                return
            
            time.sleep(5)
        
        print("⚠️  Some services may not be fully ready yet")
    
    def _display_service_urls(self):
        """Display URLs for accessing the monitoring services."""
        print("\n🌐 Service URLs:")
        print(f"   Prometheus: {self.prometheus_url}")
        print(f"   Grafana: {self.grafana_url} (admin/admin123)")
        print(f"   Alertmanager: {self.alertmanager_url}")
        print()

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prometheus Setup and Management")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "validate", "test", "reload", "targets"],
                       help="Action to perform")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="Backend URL for testing metrics endpoint")
    
    args = parser.parse_args()
    
    manager = PrometheusManager()
    
    if args.action == "start":
        success = manager.start_monitoring_stack()
        sys.exit(0 if success else 1)
        
    elif args.action == "stop":
        success = manager.stop_monitoring_stack()
        sys.exit(0 if success else 1)
        
    elif args.action == "restart":
        success = manager.restart_monitoring_stack()
        sys.exit(0 if success else 1)
        
    elif args.action == "status":
        health = manager.check_service_health()
        all_healthy = all(health.values())
        sys.exit(0 if all_healthy else 1)
        
    elif args.action == "validate":
        valid = manager.validate_configuration()
        sys.exit(0 if valid else 1)
        
    elif args.action == "test":
        success = manager.test_metrics_endpoint(args.backend_url)
        sys.exit(0 if success else 1)
        
    elif args.action == "reload":
        success = manager.reload_prometheus_config()
        sys.exit(0 if success else 1)
        
    elif args.action == "targets":
        manager.get_prometheus_targets()
        sys.exit(0)

if __name__ == "__main__":
    main()