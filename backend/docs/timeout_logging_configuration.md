# Timeout and Logging Configuration Guide

## Overview

This document describes the comprehensive timeout and logging configuration system implemented for the Suna backend. The system provides environment-specific configurations, structured logging, and robust timeout management across all services.

## Architecture

### Configuration Structure

```
backend/
├── config/
│   ├── timeout_settings.py    # Environment-specific timeout configurations
│   └── logging_settings.py    # Environment-specific logging configurations
├── middleware/
│   └── timeout_middleware.py  # Request timeout middleware
├── services/
│   └── timeout_config.py      # Service-specific timeout utilities
├── logging_config.py          # Main logging configuration
└── validate_timeout_logging_config.py  # Validation script
```

## Environment Detection

The system automatically detects the environment based on the `ENVIRONMENT` environment variable:

- `development` (default): Lenient timeouts, colored logging
- `staging`: Production-like but slightly more lenient
- `production`: Optimized for performance and reliability

## Timeout Configurations

### Service-Specific Timeouts

#### API Service
- **Development**: 5 minutes request timeout, 10 minutes WebSocket
- **Staging**: 3 minutes request timeout, 7.5 minutes WebSocket  
- **Production**: 2 minutes request timeout, 5 minutes WebSocket

#### Database
- **Development**: 30s connection, 60s query, 2 minutes transaction
- **Staging**: 15s connection, 45s query, 90s transaction
- **Production**: 10s connection, 30s query, 60s transaction

#### Redis
- **Development**: 10s connection, 30s socket timeout
- **Staging**: 8s connection, 20s socket timeout
- **Production**: 5s connection, 10s socket timeout

#### HTTP Client
- **Development**: 30s connect, 60s read, 2 minutes total
- **Staging**: 20s connect, 45s read, 90s total
- **Production**: 10s connect, 30s read, 60s total

#### Worker (Dramatiq)
- **Development**: 10 minutes task timeout
- **Staging**: 7.5 minutes task timeout
- **Production**: 5 minutes task timeout

#### RabbitMQ
- **Development**: 30s connection timeout
- **Staging**: 20s connection timeout
- **Production**: 10s connection timeout

### Usage Examples

```python
from config.timeout_settings import get_timeout_config

# Get Redis configuration
redis_config = get_timeout_config("redis")
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    socket_connect_timeout=redis_config["connection_timeout"],
    socket_timeout=redis_config["socket_timeout"]
)

# Get HTTP client configuration
from services.timeout_config import TimeoutManager
timeout_manager = TimeoutManager()
http_config = timeout_manager.get_http_client_config()

async with httpx.AsyncClient(
    timeout=httpx.Timeout(**http_config["timeout"]),
    limits=httpx.Limits(**http_config["limits"])
) as client:
    response = await client.get("https://api.example.com")
```

## Logging Configuration

### Log Levels by Environment

- **Development**: DEBUG level, colored output
- **Staging**: INFO level, structured JSON
- **Production**: INFO level, structured JSON with file rotation

### Log Formats

#### Structured (JSON)
```json
{
  "timestamp": "2025-07-28T15:09:51.162Z",
  "level": "INFO",
  "logger": "services.timeout_config",
  "message": "TimeoutManager initialized",
  "module": "timeout_config",
  "function": "__init__",
  "line": 19,
  "process": 12345,
  "thread": 67890,
  "environment": "development"
}
```

#### Colored (Development)
```
2025-07-28 15:09:51,162 - services.timeout_config - INFO - TimeoutManager initialized
```

#### Simple (Fallback)
```
INFO - TimeoutManager initialized
```

### Service-Specific Loggers

Each service has its own logger with appropriate log levels:

- **uvicorn/gunicorn**: INFO level, access logs to separate file
- **fastapi**: INFO level
- **redis**: WARNING level (reduce noise)
- **supabase**: INFO level
- **dramatiq**: INFO level
- **rabbitmq**: WARNING level
- **httpx**: WARNING level
- **websockets**: INFO level
- **sentry**: WARNING level

### Usage Examples

```python
from logging_config import get_logger, log_request_info, log_request_completion

logger = get_logger(__name__)

# Basic logging
logger.info("Service started")
logger.error("Error occurred", exc_info=True)

# Structured logging with context
logger.info("User action", extra={
    "user_id": "12345",
    "action": "login",
    "ip_address": "192.168.1.1"
})

# Request logging helpers
log_request_info(logger, "req_123", "GET", "/api/users", user_id="12345")
log_request_completion(logger, "req_123", 200, 0.123)
```

## Middleware Integration

### Timeout Middleware

The timeout middleware automatically:

- Enforces request timeouts based on endpoint type
- Logs request start and completion
- Handles timeout errors gracefully
- Tracks active requests for graceful shutdown

```python
from fastapi import FastAPI
from middleware.timeout_middleware import setup_timeout_middleware

app = FastAPI()
app = setup_timeout_middleware(app)
```

### Endpoint-Specific Timeouts

- **WebSocket endpoints**: Longer timeout (5-10 minutes)
- **Health checks**: Short timeout (10 seconds)
- **File operations**: Extended timeout (2x normal)
- **Default endpoints**: Standard timeout (2-5 minutes)

## Environment Variables

### Required Variables

```bash
# Environment detection
ENVIRONMENT=development|staging|production

# Logging configuration
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FORMAT=structured|simple|colored
LOG_DIR=logs

# Gunicorn configuration
GUNICORN_WORKERS=4
```

### Optional Variables

```bash
# Override specific timeouts (in seconds)
API_REQUEST_TIMEOUT=120
DATABASE_QUERY_TIMEOUT=30
REDIS_CONNECTION_TIMEOUT=5
HTTP_CLIENT_TIMEOUT=60
WORKER_TASK_TIMEOUT=300
```

## Docker Integration

### docker-compose.yaml

```yaml
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - LOG_FORMAT=structured
      - GUNICORN_WORKERS=4
    volumes:
      - ./backend/logs:/app/logs
```

### Service Configurations

- **Redis**: `backend/services/docker/redis.conf`
- **RabbitMQ**: `backend/services/docker/rabbitmq.conf`

## Validation and Testing

### Validation Script

Run the comprehensive validation script:

```bash
cd backend
python validate_timeout_logging_config.py
```

The script validates:

- ✅ Logging configuration setup
- ✅ Timeout configuration consistency
- ✅ Service connectivity (Redis, HTTP)
- ✅ Middleware setup
- ✅ Gunicorn configuration
- ✅ Docker configuration files

### Expected Output

```
=== Validation Summary ===
✅ Logging configuration is working correctly
✅ All timeout configurations are valid
❌ Redis connection failed: Connection refused (expected if Redis not running)
✅ HTTP client working correctly (took 2.795s)
✅ Timeout middleware setup successful
✅ Gunicorn configuration is valid
✅ All Docker configuration files exist
```

## Monitoring and Observability

### Log Files (Production)

- `logs/app.log`: General application logs
- `logs/error.log`: Error-level logs only
- `logs/access.log`: HTTP access logs
- `logs/debug.log`: Debug logs (development only)

### Metrics Integration

The timeout configurations are designed to work with:

- **Prometheus**: Timeout metrics collection
- **Grafana**: Timeout monitoring dashboards
- **Sentry**: Error tracking and alerting

### Health Checks

```python
from services.timeout_config import validate_timeout_configuration

if not validate_timeout_configuration():
    logger.error("Timeout configuration validation failed")
    # Handle configuration error
```

## Best Practices

### Development

1. Use colored logging for better readability
2. Set DEBUG log level for detailed troubleshooting
3. Use longer timeouts to avoid interrupting debugging

### Staging

1. Use production-like timeouts but slightly more lenient
2. Enable structured logging for log analysis
3. Test timeout scenarios thoroughly

### Production

1. Use optimized timeouts for performance
2. Enable file logging with rotation
3. Monitor timeout metrics and adjust as needed
4. Set up alerting for timeout-related errors

### Code Guidelines

1. Always use the centralized timeout configurations
2. Include context in log messages
3. Use structured logging for important events
4. Handle timeout errors gracefully
5. Test timeout scenarios in your code

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `backend/config/__init__.py` exists
2. **Module Not Found**: Check Python path and imports
3. **Timeout Too Short**: Adjust environment-specific settings
4. **Log Files Not Created**: Check directory permissions
5. **Middleware Not Working**: Verify FastAPI app setup

### Debug Commands

```bash
# Test logging configuration
python -c "from logging_config import setup_logging; setup_logging()"

# Test timeout configuration
python -c "from config.timeout_settings import log_timeout_summary; log_timeout_summary()"

# Validate complete setup
python validate_timeout_logging_config.py
```

## Migration Guide

### From Old Configuration

1. Replace direct timeout values with `get_timeout_config()`
2. Update logging setup to use `setup_logging()`
3. Add timeout middleware to FastAPI apps
4. Update Docker configurations
5. Run validation script to verify setup

### Example Migration

**Before:**
```python
redis_client = redis.Redis(
    host="localhost",
    socket_timeout=10.0
)
```

**After:**
```python
from config.timeout_settings import get_timeout_config

redis_config = get_timeout_config("redis")
redis_client = redis.Redis(
    host="localhost",
    socket_connect_timeout=redis_config["connection_timeout"],
    socket_timeout=redis_config["socket_timeout"]
)
```

## Support

For issues or questions about the timeout and logging configuration:

1. Run the validation script first
2. Check the logs for error details
3. Verify environment variables are set correctly
4. Ensure all configuration files exist
5. Test with different environments (development/staging/production)