#!/usr/bin/env python3
"""
Worker configuration script for FastAPI applications.

This script calculates optimal worker counts based on system resources
and deployment environment.
"""

import os
import psutil
import argparse
from pathlib import Path


class WorkerConfigurator:
    """Configures optimal worker counts for FastAPI applications."""
    
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=True)
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
    def calculate_workers(self, service_type: str = "api") -> dict:
        """Calculate optimal worker configuration."""
        
        if service_type == "api":
            # For API services: (2 * CPU) + 1 for I/O bound workloads
            workers = min((2 * self.cpu_count) + 1, 32)  # Cap at 32 workers
            worker_connections = 1000
            timeout = 120
        elif service_type == "worker":
            # For background workers: CPU count for CPU-bound tasks
            workers = max(self.cpu_count, 2)  # Minimum 2 workers
            worker_connections = 500
            timeout = 300
        else:
            # Default configuration
            workers = 4
            worker_connections = 1000
            timeout = 120
        
        # Adjust based on available memory (minimum 512MB per worker)
        max_workers_by_memory = max(int(self.memory_gb * 2), 2)
        workers = min(workers, max_workers_by_memory)
        
        return {
            "workers": workers,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "worker_connections": worker_connections,
            "timeout": timeout,
            "keep_alive": 2,
            "max_requests": 1000,
            "max_requests_jitter": 100,
            "threads": 2
        }
    
    def generate_env_config(self, service_type: str = "api") -> str:
        """Generate environment variable configuration."""
        config = self.calculate_workers(service_type)
        
        env_vars = []
        env_vars.append(f"WORKERS={config['workers']}")
        env_vars.append(f"WORKER_CLASS={config['worker_class']}")
        env_vars.append(f"WORKER_CONNECTIONS={config['worker_connections']}")
        env_vars.append(f"TIMEOUT={config['timeout']}")
        env_vars.append(f"KEEPALIVE={config['keep_alive']}")
        env_vars.append(f"MAX_REQUESTS={config['max_requests']}")
        env_vars.append(f"MAX_REQUESTS_JITTER={config['max_requests_jitter']}")
        env_vars.append(f"THREADS={config['threads']}")
        
        return "\n".join(env_vars)
    
    def generate_gunicorn_config(self, service_type: str = "api", app_module: str = "app.main:app") -> str:
        """Generate gunicorn configuration file."""
        config = self.calculate_workers(service_type)
        
        gunicorn_config = f"""# Gunicorn configuration for {service_type}
# Auto-generated based on system resources

bind = "0.0.0.0:8000"
workers = {config['workers']}
worker_class = "{config['worker_class']}"
worker_connections = {config['worker_connections']}
timeout = {config['timeout']}
keepalive = {config['keep_alive']}
max_requests = {config['max_requests']}
max_requests_jitter = {config['max_requests_jitter']}

# Performance optimizations
preload_app = True
worker_tmp_dir = "/dev/shm"

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
capture_output = True

# Graceful shutdown
graceful_timeout = 30

# Security
forwarded_allow_ips = "*"
"""
        return gunicorn_config
    
    def update_dockerfile(self, dockerfile_path: str, service_type: str = "api"):
        """Update Dockerfile with optimal worker configuration."""
        config = self.calculate_workers(service_type)
        
        if not Path(dockerfile_path).exists():
            print(f"Dockerfile not found: {dockerfile_path}")
            return False
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Update environment variables in Dockerfile
        env_updates = []
        for key, value in config.items():
            env_line = f"ENV {key.upper()}={value}"
            env_updates.append(env_line)
        
        # Add environment variables before CMD
        env_section = "\n".join(env_updates)
        
        if "ENV WORKERS=" in content:
            # Replace existing worker configuration
            lines = content.split('\n')
            new_lines = []
            skip_env = False
            
            for line in lines:
                if line.startswith("ENV WORKERS="):
                    skip_env = True
                    new_lines.append(env_section)
                elif skip_env and (line.startswith("ENV ") and any(key.upper() in line for key in config.keys())):
                    continue  # Skip old env vars
                elif skip_env and not line.startswith("ENV "):
                    skip_env = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
        else:
            # Add environment variables before CMD
            content = content.replace("# Comando para iniciar", f"{env_section}\n\n# Comando para iniciar")
        
        with open(dockerfile_path, 'w') as f:
            f.write(content)
        
        print(f"Updated {dockerfile_path} with {config['workers']} workers")
        return True
    
    def print_system_info(self):
        """Print system information for worker calculation."""
        print("=== System Information ===")
        print(f"CPU Cores: {self.cpu_count}")
        print(f"Memory: {self.memory_gb:.1f} GB")
        print(f"Platform: {os.name}")
        print()
    
    def print_recommendations(self):
        """Print worker recommendations for different services."""
        print("=== Worker Recommendations ===")
        
        api_config = self.calculate_workers("api")
        worker_config = self.calculate_workers("worker")
        
        print(f"API Service (I/O bound):")
        print(f"  Workers: {api_config['workers']}")
        print(f"  Connections per worker: {api_config['worker_connections']}")
        print(f"  Timeout: {api_config['timeout']}s")
        print()
        
        print(f"Background Workers (CPU bound):")
        print(f"  Workers: {worker_config['workers']}")
        print(f"  Connections per worker: {worker_config['worker_connections']}")
        print(f"  Timeout: {worker_config['timeout']}s")
        print()


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Configure FastAPI workers")
    parser.add_argument("--service", choices=["api", "worker"], default="api",
                       help="Service type to configure")
    parser.add_argument("--dockerfile", help="Path to Dockerfile to update")
    parser.add_argument("--env-file", help="Path to write environment variables")
    parser.add_argument("--gunicorn-config", help="Path to write gunicorn config")
    parser.add_argument("--info", action="store_true", help="Show system info and recommendations")
    
    args = parser.parse_args()
    
    configurator = WorkerConfigurator()
    
    if args.info:
        configurator.print_system_info()
        configurator.print_recommendations()
        return
    
    if args.dockerfile:
        configurator.update_dockerfile(args.dockerfile, args.service)
    
    if args.env_file:
        env_config = configurator.generate_env_config(args.service)
        with open(args.env_file, 'w') as f:
            f.write(env_config)
        print(f"Environment configuration written to {args.env_file}")
    
    if args.gunicorn_config:
        gunicorn_config = configurator.generate_gunicorn_config(args.service)
        with open(args.gunicorn_config, 'w') as f:
            f.write(gunicorn_config)
        print(f"Gunicorn configuration written to {args.gunicorn_config}")


if __name__ == "__main__":
    main()