# Gunicorn configuration for api
# Auto-generated based on system resources

bind = "0.0.0.0:8000"
workers = 9
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

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
