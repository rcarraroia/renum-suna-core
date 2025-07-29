"""
Prometheus metrics middleware for FastAPI.

This middleware automatically collects HTTP request metrics including
request count, duration, size, and response size.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from services.metrics import get_metrics_collector
from logging_config import get_logger

logger = get_logger(__name__)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.metrics = get_metrics_collector()
        self.exclude_paths = exclude_paths or ['/metrics', '/health', '/docs', '/openapi.json']
        logger.info("Prometheus metrics middleware initialized", extra={
            "exclude_paths": self.exclude_paths
        })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        
        # Skip metrics collection for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Extract request information
        method = request.method
        path = self._normalize_path(request.url.path)
        request_size = self._get_request_size(request)
        
        # Start timing
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Calculate metrics
            duration = time.time() - start_time
            response_size = self._get_response_size(response)
            
            # Record metrics
            self.metrics.record_http_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration,
                request_size=request_size,
                response_size=response_size
            )
            
            # Log request completion
            logger.debug("HTTP request completed", extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration": duration,
                "request_size": request_size,
                "response_size": response_size
            })
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            
            # Determine status code from exception
            status_code = getattr(e, 'status_code', 500)
            
            self.metrics.record_http_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration,
                request_size=request_size
            )
            
            # Record error
            self.metrics.record_error(
                error_type=type(e).__name__,
                component="http_middleware"
            )
            
            logger.error("HTTP request failed", extra={
                "method": method,
                "path": path,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": duration
            })
            
            raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from metrics."""
        return any(excluded in path for excluded in self.exclude_paths)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics to avoid high cardinality."""
        
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Normalize common patterns to reduce cardinality
        path_segments = path.split('/')
        normalized_segments = []
        
        for segment in path_segments:
            # Replace UUIDs and IDs with placeholders
            if self._looks_like_uuid(segment):
                normalized_segments.append('{uuid}')
            elif self._looks_like_id(segment):
                normalized_segments.append('{id}')
            else:
                normalized_segments.append(segment)
        
        normalized_path = '/'.join(normalized_segments)
        
        # Limit path length to prevent memory issues
        if len(normalized_path) > 100:
            normalized_path = normalized_path[:97] + '...'
        
        return normalized_path
    
    def _looks_like_uuid(self, segment: str) -> bool:
        """Check if segment looks like a UUID."""
        if len(segment) != 36:
            return False
        
        # Simple UUID pattern check
        parts = segment.split('-')
        if len(parts) != 5:
            return False
        
        expected_lengths = [8, 4, 4, 4, 12]
        for part, expected_length in zip(parts, expected_lengths):
            if len(part) != expected_length or not all(c.isalnum() for c in part):
                return False
        
        return True
    
    def _looks_like_id(self, segment: str) -> bool:
        """Check if segment looks like a numeric ID."""
        return segment.isdigit() and len(segment) > 0
    
    def _get_request_size(self, request: Request) -> int:
        """Get request size in bytes."""
        try:
            content_length = request.headers.get('content-length')
            if content_length:
                return int(content_length)
            
            # For requests without content-length, estimate from headers
            header_size = sum(len(k) + len(v) for k, v in request.headers.items())
            return header_size + len(str(request.url))
            
        except (ValueError, TypeError):
            return 0
    
    def _get_response_size(self, response: Response) -> int:
        """Get response size in bytes."""
        try:
            # Try to get content-length from headers
            content_length = response.headers.get('content-length')
            if content_length:
                return int(content_length)
            
            # For streaming responses or responses without content-length
            if hasattr(response, 'body') and response.body:
                return len(response.body)
            
            # Estimate from headers if body is not available
            header_size = sum(len(k) + len(v) for k, v in response.headers.items())
            return header_size
            
        except (ValueError, TypeError, AttributeError):
            return 0


def setup_metrics_middleware(app, exclude_paths: list = None):
    """Setup Prometheus metrics middleware for the application."""
    
    # Add metrics middleware
    app.add_middleware(PrometheusMetricsMiddleware, exclude_paths=exclude_paths)
    
    logger.info("Prometheus metrics middleware setup completed")
    
    return app