# Gunicorn configuration for api
# Enhanced configuration with proper timeouts and logging

import os
try:
    from config.timeout_settings import get_timeout_config
except ImportError:
    from logging_config import get_timeout_config

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout configurations from centralized config
api_timeouts = get_timeout_config("api")
timeout = int(api_timeouts.get("request_timeout", 120))
keepalive = int(api_timeouts.get("keep_alive", 2))
graceful_timeout = int(api_timeouts.get("graceful_shutdown", 30))

# Performance optimizations
preload_app = True
worker_tmp_dir = "/dev/shm"

# Logging configuration
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True

# Access log format with structured data
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Process naming
proc_name = "suna-backend"

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Suna Backend with enhanced configuration")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Suna Backend workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received INT/QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker {worker.pid} about to be forked")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} spawned")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT signal")
