"""
Timeout middleware for Renum backend.

This middleware implements request timeouts and structured logging
for the Renum backend application.
"""

import asyncio
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger, get_timeout_config

logger = get_logger(__name__)


class RenumTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to handle request timeouts for Renum backend."""
    
    def __init__(self, app, default_timeout: float = 120.0):
        super().__init__(app)
        self.default_timeout = default_timeout
        self.timeout_config = get_timeout_config("api")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timeout handling."""
        
        # Get timeout for this request
        timeout = self._get_request_timeout(request)
        
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            
            # Log successful request
            execution_time = time.time() - start_time
            logger.info(
                "Renum request completed successfully",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "execution_time": execution_time,
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(
                "Renum request timeout exceeded",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "timeout": timeout,
                    "execution_time": execution_time
                }
            )
            
            raise HTTPException(
                status_code=408,
                detail={
                    "error": "Request timeout",
                    "timeout": timeout,
                    "execution_time": execution_time,
                    "service": "renum-backend"
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Renum request failed with exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "execution_time": execution_time,
                    "exception": str(e)
                }
            )
            raise
    
    def _get_request_timeout(self, request: Request) -> float:
        """Get timeout for specific request based on path and method."""
        
        path = request.url.path
        method = request.method
        
        # Special timeouts for Renum-specific endpoints
        if "/api/teams/execute" in path:
            return self.timeout_config.get("request_timeout", 600.0)  # 10 minutes for team execution
        elif "/api/websocket" in path or "/ws" in path:
            return self.timeout_config.get("request_timeout", 300.0)  # 5 minutes for WebSocket
        elif "/api/teams" in path and method == "POST":
            return self.timeout_config.get("request_timeout", 180.0)  # 3 minutes for team creation
        elif method == "POST" and "/api/" in path:
            return self.timeout_config.get("request_timeout", 120.0)  # 2 minutes for POST requests
        else:
            return self.timeout_config.get("request_timeout", self.default_timeout)


class RenumRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging in Renum backend."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details with Renum-specific context."""
        
        # Generate request ID
        request_id = f"renum_req_{int(time.time() * 1000)}"
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Extract additional context
        team_id = request.headers.get("X-Team-ID")
        user_id = request.headers.get("X-User-ID")
        
        # Log incoming request
        logger.info(
            "Incoming Renum request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
                "team_id": team_id,
                "user_id": user_id
            }
        )
        
        try:
            response = await call_next(request)
            
            execution_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Renum request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "execution_time": execution_time,
                    "team_id": team_id,
                    "user_id": user_id
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Service"] = "renum-backend"
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Renum request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "execution_time": execution_time,
                    "exception": str(e),
                    "team_id": team_id,
                    "user_id": user_id
                }
            )
            
            raise