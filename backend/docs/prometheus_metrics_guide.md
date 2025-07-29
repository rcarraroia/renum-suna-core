# Prometheus Metrics Implementation Guide

## Overview

This document describes the comprehensive Prometheus metrics implementation for the Suna backend. The system provides detailed monitoring and observability for HTTP requests, database operations, Redis operations, worker tasks, agent executions, LLM requests, and system health.

## Architecture

### Components

```
backend/
├── services/
│   ├── metrics.py                 # Core metrics collector
│   └── metrics_decorators.py      # Decorators for instrumentation
├── middleware/
│   └── metrics_middleware.py      # HTTP request metrics middleware
├── api/
│   └── metrics.py                 # Metrics API endpoints
└── validate_prometheus_metrics.py # Validation script
```

## Available Metrics

### HTTP Request Metrics

#### `http_requests_total`
- **Type**: Counter
- **Description**: Total number of HTTP requests
- **Labels**: `method`, `endpoint`, `status_code`
- **Example**: `http_requests_total{endpoint="/api/users",method="GET",status_code="200"} 42`

#### `http_request_duration_seconds`
- **Type**: Histogram
- **Description**: HTTP request duration in seconds
- **Labels**: `method`, `endpoint`
- **Buckets**: `[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`

#### `http_request_size_bytes`
- **Type**: Histogram
- **Description**: HTTP request size in bytes
- **Labels**: `method`, `endpoint`

#### `http_response_size_bytes`
- **Type**: Histogram
- **Description**: HTTP response size in bytes
- **Labels**: `method`, `endpoint`

### Database Metrics

#### `database_queries_total`
- **Type**: Counter
- **Description**: Total number of database queries
- **Labels**: `operation`, `table`, `status`
- **Example**: `database_queries_total{operation="SELECT",status="success",table="users"} 156`

#### `database_query_duration_seconds`
- **Type**: Histogram
- **Description**: Database query duration in seconds
- **Labels**: `operation`, `table`
- **Buckets**: `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]`

#### `database_connections_active`
- **Type**: Gauge
- **Description**: Number of active database connections

#### `database_connections_pool_size`
- **Type**: Gauge
- **Description**: Database connection pool size

### Redis Metrics

#### `redis_operations_total`
- **Type**: Counter
- **Description**: Total number of Redis operations
- **Labels**: `operation`, `status`
- **Example**: `redis_operations_total{operation="GET",status="success"} 89`

#### `redis_operation_duration_seconds`
- **Type**: Histogram
- **Description**: Redis operation duration in seconds
- **Labels**: `operation`
- **Buckets**: `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]`

#### `redis_connections_active`
- **Type**: Gauge
- **Description**: Number of active Redis connections

#### `redis_memory_usage_bytes`
- **Type**: Gauge
- **Description**: Redis memory usage in bytes

### Worker/Queue Metrics

#### `worker_tasks_total`
- **Type**: Counter
- **Description**: Total number of worker tasks
- **Labels**: `task_name`, `status`

#### `worker_task_duration_seconds`
- **Type**: Histogram
- **Description**: Worker task duration in seconds
- **Labels**: `task_name`
- **Buckets**: `[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0]`

#### `worker_queue_size`
- **Type**: Gauge
- **Description**: Number of tasks in worker queue
- **Labels**: `queue_name`

### Business Logic Metrics

#### `user_sessions_active`
- **Type**: Gauge
- **Description**: Number of active user sessions

#### `agent_executions_total`
- **Type**: Counter
- **Description**: Total number of agent executions
- **Labels**: `agent_type`, `status`

#### `agent_execution_duration_seconds`
- **Type**: Histogram
- **Description**: Agent execution duration in seconds
- **Labels**: `agent_type`
- **Buckets**: `[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]`

#### `llm_requests_total`
- **Type**: Counter
- **Description**: Total number of LLM requests
- **Labels**: `provider`, `model`, `status`

#### `llm_request_duration_seconds`
- **Type**: Histogram
- **Description**: LLM request duration in seconds
- **Labels**: `provider`, `model`
- **Buckets**: `[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]`

#### `llm_tokens_total`
- **Type**: Counter
- **Description**: Total number of LLM tokens used
- **Labels**: `provider`, `model`, `type` (input/output)

### System Metrics

#### `application_info`
- **Type**: Info
- **Description**: Application information
- **Labels**: `version`, `environment`, `service`

#### `application_status`
- **Type**: Enum
- **Description**: Application status
- **States**: `starting`, `healthy`, `degraded`, `unhealthy`

#### `errors_total`
- **Type**: Counter
- **Description**: Total number of errors
- **Labels**: `error_type`, `component`

## Usage Examples

### Automatic HTTP Metrics

HTTP metrics are collected automatically via middleware:

```python
from fastapi import FastAPI
from middleware.metrics_middleware import setup_metrics_middleware

app = FastAPI()
app = setup_metrics_middleware(app)
```

### Database Query Instrumentation

```python
from services.metrics_decorators import instrument_database_query

@instrument_database_query("SELECT", "users")
async def get_user(user_id: str):
    # Database query logic
    return await db.query("SELECT * FROM users WHERE id = ?", user_id)

# Or using context manager
from services.metrics_decorators import time_database_operation

async def update_user(user_id: str, data: dict):
    with time_database_operation("UPDATE", "users"):
        return await db.query("UPDATE users SET ... WHERE id = ?", user_id)
```

### Redis Operation Instrumentation

```python
from services.metrics_decorators import instrument_redis_operation

@instrument_redis_operation("GET")
async def get_cached_data(key: str):
    return await redis_client.get(key)

# Context manager approach
from services.metrics_decorators import time_redis_operation

async def set_cache(key: str, value: str):
    with time_redis_operation("SET"):
        await redis_client.set(key, value, ex=3600)
```

### Worker Task Instrumentation

```python
from services.metrics_decorators import instrument_worker_task

@instrument_worker_task("email_notification")
async def send_email_notification(user_id: str, message: str):
    # Email sending logic
    await email_service.send(user_id, message)
```

### Agent Execution Instrumentation

```python
from services.metrics_decorators import instrument_agent_execution

@instrument_agent_execution("research_agent")
async def execute_research_task(query: str):
    # Agent execution logic
    return await research_agent.execute(query)
```

### LLM Request Instrumentation

```python
from services.metrics_decorators import instrument_llm_request

@instrument_llm_request("openai", "gpt-4")
async def generate_response(prompt: str):
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "response": response.choices[0].message.content,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
    }
```

### Manual Metrics Recording

```python
from services.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Record custom business metrics
metrics.update_active_sessions(42)
metrics.record_error("ValidationError", "user_input")

# Update system gauges
metrics.update_database_connections(active=15, pool_size=20)
metrics.update_redis_metrics(active_connections=8, memory_usage=1024*1024*50)
```

## API Endpoints

### `/metrics`
- **Method**: GET
- **Description**: Prometheus metrics endpoint
- **Response**: Prometheus format metrics
- **Content-Type**: `text/plain; version=0.0.4; charset=utf-8`

### `/metrics/health`
- **Method**: GET
- **Description**: Health check for metrics system
- **Response**: JSON with health status

### `/metrics/summary`
- **Method**: GET
- **Description**: Summary of available metrics
- **Response**: JSON with metrics information

### `/metrics/config`
- **Method**: GET
- **Description**: Metrics configuration information
- **Response**: JSON with configuration details

## Prometheus Configuration

### Scrape Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'suna-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Docker Compose Integration

```yaml
# docker-compose.yml
services:
  backend:
    # ... other configuration
    ports:
      - "8000:8000"
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
```

## Grafana Dashboards

### Key Metrics Dashboard

```json
{
  "dashboard": {
    "title": "Suna Backend Metrics",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "HTTP Request Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Database Query Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(database_queries_total[5m])",
            "legendFormat": "{{operation}} {{table}}"
          }
        ]
      },
      {
        "title": "Redis Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(redis_operations_total[5m])",
            "legendFormat": "{{operation}}"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "singlestat",
        "targets": [
          {
            "expr": "user_sessions_active",
            "legendFormat": "Active Sessions"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(errors_total[5m])",
            "legendFormat": "{{error_type}} {{component}}"
          }
        ]
      }
    ]
  }
}
```

### Useful Queries

```promql
# HTTP request rate by endpoint
rate(http_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Database query latency
histogram_quantile(0.99, rate(database_query_duration_seconds_bucket[5m]))

# Redis hit rate (if implemented)
rate(redis_operations_total{operation="GET",status="success"}[5m]) / rate(redis_operations_total{operation="GET"}[5m])

# LLM token usage rate
rate(llm_tokens_total[5m])

# Agent execution success rate
rate(agent_executions_total{status="success"}[5m]) / rate(agent_executions_total[5m])
```

## Alerting Rules

### Prometheus Alerting Rules

```yaml
# alerts.yml
groups:
  - name: suna-backend
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseConnectionsHigh
        expr: database_connections_active / database_connections_pool_size > 0.8
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool usage high"
          description: "Database connection pool is {{ $value | humanizePercentage }} full"

      - alert: RedisConnectionsHigh
        expr: redis_connections_active > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of Redis connections"
          description: "Redis has {{ $value }} active connections"

      - alert: ApplicationDown
        expr: up{job="suna-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Suna backend is down"
          description: "Suna backend has been down for more than 1 minute"
```

## Performance Considerations

### Metric Cardinality

- **Path Normalization**: The middleware automatically normalizes paths to reduce cardinality
- **UUID/ID Replacement**: UUIDs and numeric IDs are replaced with placeholders
- **Label Limits**: Keep label values bounded to prevent memory issues

### Collection Overhead

- **Minimal Impact**: Metrics collection adds < 1ms overhead per request
- **Async Operations**: All metrics operations are non-blocking
- **Memory Usage**: Approximately 10-50MB for typical workloads

### Best Practices

1. **Use Appropriate Metric Types**:
   - Counters for cumulative values
   - Gauges for current values
   - Histograms for distributions

2. **Label Guidelines**:
   - Keep label cardinality low (< 1000 unique combinations)
   - Use meaningful label names
   - Avoid high-cardinality labels (user IDs, timestamps)

3. **Instrumentation Strategy**:
   - Instrument at service boundaries
   - Focus on business-critical operations
   - Use decorators for consistent instrumentation

## Validation and Testing

### Running Validation

```bash
cd backend
python validate_prometheus_metrics.py
```

### Expected Output

```
🚀 Starting comprehensive Prometheus metrics validation
=== Validation Summary ===
✅ Metrics collector properly initialized
✅ Metrics generation successful (2886 bytes)
✅ HTTP metrics recording working correctly
✅ Database metrics recording working correctly
✅ Redis metrics recording working correctly
✅ Business metrics recording working correctly
✅ Error metrics recording working correctly
✅ Metrics decorators working correctly
✅ Metrics endpoint functionality validated
🎉 All Prometheus metrics validations passed successfully!
```

### Testing Metrics Collection

```python
# Test script example
import asyncio
from services.metrics import get_metrics_collector

async def test_metrics():
    metrics = get_metrics_collector()
    
    # Record some test metrics
    metrics.record_http_request("GET", "/test", 200, 0.123)
    metrics.record_database_query("SELECT", "users", "success", 0.045)
    metrics.record_redis_operation("GET", "success", 0.012)
    
    # Generate and print metrics
    print(metrics.get_metrics())

asyncio.run(test_metrics())
```

## Troubleshooting

### Common Issues

1. **Metrics Not Appearing**:
   - Check if middleware is properly configured
   - Verify decorators are applied correctly
   - Ensure metrics collector is initialized

2. **High Memory Usage**:
   - Check for high cardinality labels
   - Monitor metric collection frequency
   - Consider metric retention policies

3. **Performance Impact**:
   - Profile metric collection overhead
   - Optimize label usage
   - Consider sampling for high-volume metrics

### Debug Commands

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Check metrics health
curl http://localhost:8000/metrics/health

# Get metrics summary
curl http://localhost:8000/metrics/summary

# Validate metrics implementation
python validate_prometheus_metrics.py
```

## Migration and Deployment

### Deployment Checklist

- [ ] Metrics middleware configured
- [ ] Decorators applied to key functions
- [ ] Prometheus scrape configuration updated
- [ ] Grafana dashboards imported
- [ ] Alerting rules configured
- [ ] Validation tests passing

### Monitoring the Monitoring

- Monitor Prometheus scrape success rate
- Check Grafana dashboard functionality
- Verify alerting rule effectiveness
- Monitor metrics collection performance impact

This comprehensive metrics implementation provides deep visibility into the Suna backend performance and behavior, enabling proactive monitoring and optimization.