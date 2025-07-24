"""
Middlewares para a aplicação.

Este módulo contém middlewares para autenticação, logging e outras funcionalidades.
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.auth import decode_token

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticação de requisições."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Processa a requisição.
        
        Args:
            request: Requisição HTTP
            call_next: Próxima função a ser chamada
            
        Returns:
            Resposta HTTP
        """
        # Ignora rotas públicas
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Verifica o token de autenticação
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        try:
            # Extrai o token
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )
            
            # Decodifica o token
            payload = decode_token(token)
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token"}
                )
            
            # Adiciona o payload do token ao request state
            request.state.user = payload
            
            # Continua o processamento
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requisições."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Processa a requisição.
        
        Args:
            request: Requisição HTTP
            call_next: Próxima função a ser chamada
            
        Returns:
            Resposta HTTP
        """
        # Gera um ID único para a requisição
        request_id = str(uuid.uuid4())
        
        # Adiciona o ID da requisição ao contexto do logger
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        # Registra o tempo de início
        start_time = time.time()
        
        try:
            # Chama o próximo middleware ou endpoint
            response = await call_next(request)
            
            # Calcula o tempo de processamento
            process_time = time.time() - start_time
            
            # Registra o log de conclusão
            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s",
                extra={"request_id": request_id}
            )
            
            return response
        
        except Exception as e:
            # Calcula o tempo de processamento
            process_time = time.time() - start_time
            
            # Registra o log de erro
            logger.error(
                f"Request failed: {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.4f}s",
                extra={"request_id": request_id}
            )
            
            # Retorna uma resposta de erro
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )