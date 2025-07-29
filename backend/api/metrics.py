"""
Metrics API endpoints for Prometheus scraping.

This module provides endpoints for exposing Prometheus metrics
and health check information.
"""

from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import PlainTextResponse
from services.metrics import get_metrics_collector, CONTENT_TYPE_LATEST
from logging_config import get_logger
import json
from typing import Dict, Any

logger = get_logger(__name__)
router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for scraping.
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics_data = metrics_collector.get_metrics()
        
        logger.debug("Metrics endpoint accessed", extra={
            "metrics_size": len(metrics_data)
        })
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        logger.error("Failed to generate metrics", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        # Record error in metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_error(
            error_type=type(e).__name__,
            component="metrics_endpoint"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics"
        )


@router.get("/metrics/health")
async def get_metrics_health():
    """
    Health check endpoint for metrics system.
    
    Returns the health status of the metrics collection system.
    """
    try:
        metrics_collector = get_metrics_collector()
        
        # Basic health check - try to generate metrics
        metrics_data = metrics_collector.get_metrics()
        
        health_info = {
            "status": "healthy",
            "metrics_available": True,
            "metrics_size_bytes": len(metrics_data),
            "registry_collectors": len(metrics_collector.registry._collector_to_names),
            "timestamp": "2025-07-28T15:00:00Z"  # This should be actual timestamp
        }
        
        logger.debug("Metrics health check completed", extra=health_info)
        
        return health_info
        
    except Exception as e:
        logger.error("Metrics health check failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        health_info = {
            "status": "unhealthy",
            "metrics_available": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": "2025-07-28T15:00:00Z"  # This should be actual timestamp
        }
        
        return health_info


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Get a summary of available metrics.
    
    Returns information about all registered metrics and their current values.
    """
    try:
        metrics_collector = get_metrics_collector()
        
        # Get basic registry information
        registry_info = {
            "total_collectors": len(metrics_collector.registry._collector_to_names),
            "collector_names": list(metrics_collector.registry._collector_to_names.values())
        }
        
        # Get sample of current metric values (this is simplified)
        sample_metrics = {
            "http_requests_total": "Available",
            "http_request_duration_seconds": "Available",
            "database_queries_total": "Available",
            "redis_operations_total": "Available",
            "worker_tasks_total": "Available",
            "agent_executions_total": "Available",
            "llm_requests_total": "Available",
            "errors_total": "Available"
        }
        
        summary = {
            "status": "active",
            "registry_info": registry_info,
            "available_metrics": sample_metrics,
            "metrics_categories": [
                "http_requests",
                "database_operations", 
                "redis_operations",
                "worker_tasks",
                "agent_executions",
                "llm_requests",
                "system_metrics",
                "error_tracking"
            ]
        }
        
        logger.debug("Metrics summary generated", extra={
            "total_collectors": registry_info["total_collectors"],
            "categories": len(summary["metrics_categories"])
        })
        
        return summary
        
    except Exception as e:
        logger.error("Failed to generate metrics summary", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics summary"
        )


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset all metrics (development/testing only).
    
    This endpoint should only be available in development environments.
    """
    try:
        # This is a simplified reset - in practice, you might want to
        # recreate the metrics collector or clear specific metrics
        logger.warning("Metrics reset requested - this should only be used in development")
        
        return {
            "status": "reset_requested",
            "message": "Metrics reset functionality not implemented for safety",
            "recommendation": "Restart the application to reset metrics"
        }
        
    except Exception as e:
        logger.error("Failed to reset metrics", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to reset metrics"
        )


# Additional utility endpoints for debugging

@router.get("/metrics/config")
async def get_metrics_config():
    """
    Get metrics configuration information.
    
    Returns configuration details about the metrics system.
    """
    try:
        config_info = {
            "prometheus_client_version": "0.21.1",  # Should come from package info
            "metrics_enabled": True,
            "collection_interval": "on_request",
            "storage_type": "in_memory",
            "export_format": "prometheus",
            "middleware_enabled": True,
            "excluded_paths": ["/metrics", "/health", "/docs", "/openapi.json"]
        }
        
        logger.debug("Metrics configuration requested")
        
        return config_info
        
    except Exception as e:
        logger.error("Failed to get metrics configuration", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get metrics configuration"
        )