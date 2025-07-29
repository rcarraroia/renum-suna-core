"""
Timeout middleware for FastAPI applications.

This middleware enforces request timeouts and provides graceful handling
of timeout scenarios with proper logging and error responses.
"""

import asyncio
import time
from datetime import datetime
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from logging_config import get_logger, get_timeout_config, log_request_info, log_request_completion, log_error_with_context

logger = get_logger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts."""
    
    def __init__(self, app, timeout: float = None):
        super().__init__(app)
        api_config = get_timeout_config("api")
        self.timeout = timeout or api_config.get("request_timeout", 120.0)
        self.client_timeout = api_config.get("client_timeout", 60.0)
        
        logger.info("Timeout middleware initialized", extra={
            "request_timeout": self.timeout,
            "client_timeout": self.client_timeout
        })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timeout enforcement."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', f"req_{int(time.time() * 1000)}")
        
        # Set request_id if not already set
        if not hasattr(request.state, 'request_id'):
            request.state.request_id = request_id
        
        # Determine timeout based on endpoint
        timeout = self._get_endpoint_timeout(request)
        
        # Log request start
        log_request_info(
            logger, request_id, request.method, str(request.url.path),
            timeout=timeout,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            
            # Log successful request completion
            duration = time.time() - start_time
            log_request_completion(
                logger, request_id, response.status_code, duration,
                timeout=timeout,
                path=str(request.url.path),
                method=request.method
            )
            
            return response
            
        except asyncio.TimeoutError:
            # Handle timeout
            duration = time.time() - start_time
            logger.warning("Request timeout exceeded", extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "duration": duration,
                "timeout": timeout,
                "error_type": "TimeoutError"
            })
            
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request timeout",
                    "message": f"Request exceeded timeout of {timeout} seconds",
                    "timeout": timeout,
                    "duration": duration,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            
        except Exception as e:
            # Handle other errors
            duration = time.time() - start_time
            log_error_with_context(logger, e, {
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "duration": duration,
                "timeout": timeout
            })
            raise
    
    def _get_endpoint_timeout(self, request: Request) -> float:
        """Get timeout for specific endpoint."""
        path = request.url.path
        method = request.method
        
        # WebSocket endpoints get longer timeout
        if path.startswith("/ws") or "websocket" in path.lower():
            api_config = get_timeout_config("api")
            return api_config.get("websocket_timeout", 300.0)
        
        # Health check endpoints get shorter timeout
        if path in ["/api/health", "/api/health-docker"]:
            return 10.0
        
        # File upload/download endpoints get longer timeout
        if any(keyword in path.lower() for keyword in ["upload", "download", "file"]):
            return self.timeout * 2
        
        # Default timeout
        return self.timeout


class GracefulShutdownHandler:
    """Handles graceful shutdown with proper timeout management."""
    
    def __init__(self):
        api_config = get_timeout_config("api")
        self.shutdown_timeout = api_config.get("graceful_shutdown", 30.0)
        self.active_requests = set()
        self.shutdown_initiated = False
        
        logger.info("Graceful shutdown handler initialized", extra={
            "shutdown_timeout": self.shutdown_timeout
        })
    
    def add_request(self, request_id: str):
        """Add active request to tracking."""
        if not self.shutdown_initiated:
            self.active_requests.add(request_id)
    
    def remove_request(self, request_id: str):
        """Remove completed request from tracking."""
        self.active_requests.discard(request_id)
    
    async def initiate_shutdown(self):
        """Initiate graceful shutdown process."""
        self.shutdown_initiated = True
        logger.info("Graceful shutdown initiated", extra={
            "active_requests": len(self.active_requests),
            "shutdown_timeout": self.shutdown_timeout
        })
        
        # Wait for active requests to complete
        start_time = time.time()
        while self.active_requests and (time.time() - start_time) < self.shutdown_timeout:
            logger.info("Waiting for active requests to complete", extra={
                "remaining_requests": len(self.active_requests),
                "elapsed_time": time.time() - start_time
            })
            await asyncio.sleep(1.0)
        
        if self.active_requests:
            logger.warning("Shutdown timeout reached with active requests", extra={
                "remaining_requests": len(self.active_requests),
                "timeout": self.shutdown_timeout
            })
        else:
            logger.info("All requests completed, shutdown proceeding")


# Global shutdown handler
shutdown_handler = GracefulShutdownHandler()


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track active requests for graceful shutdown."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request lifecycle."""
        request_id = getattr(request.state, 'request_id', f"req_{int(time.time() * 1000)}")
        
        # Add request to tracking
        shutdown_handler.add_request(request_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Remove request from tracking
            shutdown_handler.remove_request(request_id)


def setup_timeout_middleware(app):
    """Setup timeout-related middleware for the application."""
    # Add request tracking middleware
    app.add_middleware(RequestTrackingMiddleware)
    
    # Add timeout middleware
    app.add_middleware(TimeoutMiddleware)
    
    logger.info("Timeout middleware setup completed")
    
    return app