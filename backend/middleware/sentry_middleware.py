"""
Middleware para integração aprimorada com Sentry
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk import Hub
import time
import uuid
from typing import Callable
from utils.sentry_utils import (
    set_request_context,
    add_breadcrumb,
    capture_exception_with_context
)
from utils.logger import logger

class SentryMiddleware:
    """
    Middleware para capturar automaticamente informações de requisições
    e erros para o Sentry
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())[:8]
        
        # Configurar contexto do Sentry para esta requisição
        with Hub(Hub.current) as hub:
            with hub.configure_scope() as scope_obj:
                # Adicionar informações da requisição
                scope_obj.set_tag("request_id", request_id)
                scope_obj.set_context("request", {
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "request_id": request_id
                })
                
                # Adicionar headers seguros (sem informações sensíveis)
                safe_headers = {}
                for key, value in request.headers.items():
                    if key.lower() not in ['authorization', 'cookie', 'x-api-key']:
                        safe_headers[key] = value
                
                scope_obj.set_context("headers", safe_headers)
                
                # Adicionar breadcrumb inicial
                add_breadcrumb(
                    f"{request.method} {request.url.path}",
                    category="http",
                    data={
                        "method": request.method,
                        "url": str(request.url),
                        "request_id": request_id
                    }
                )
                
                start_time = time.time()
                
                try:
                    # Processar requisição
                    response = await self._process_request(request, send)
                    
                    # Calcular tempo de resposta
                    duration = time.time() - start_time
                    
                    # Adicionar métricas de performance
                    scope_obj.set_context("performance", {
                        "duration_ms": round(duration * 1000, 2),
                        "status_code": getattr(response, 'status_code', 'unknown')
                    })
                    
                    # Adicionar breadcrumb de sucesso
                    add_breadcrumb(
                        f"Request completed: {getattr(response, 'status_code', 'unknown')}",
                        category="http",
                        data={
                            "status_code": getattr(response, 'status_code', 'unknown'),
                            "duration_ms": round(duration * 1000, 2)
                        }
                    )
                    
                    return response
                    
                except Exception as e:
                    # Calcular tempo até o erro
                    duration = time.time() - start_time
                    
                    # Capturar exceção com contexto completo
                    capture_exception_with_context(
                        e,
                        context={
                            "request": {
                                "method": request.method,
                                "url": str(request.url),
                                "path": request.url.path,
                                "request_id": request_id,
                                "duration_ms": round(duration * 1000, 2)
                            }
                        },
                        tags={
                            "component": "http_middleware",
                            "request_method": request.method,
                            "request_path": request.url.path
                        }
                    )
                    
                    # Re-raise para que o FastAPI possa processar
                    raise
    
    async def _process_request(self, request: Request, send):
        """
        Processa a requisição através da aplicação
        """
        response_started = False
        status_code = None
        
        async def send_wrapper(message):
            nonlocal response_started, status_code
            
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
            
            await send(message)
        
        # Criar um scope modificado para passar o request_id
        scope = request.scope.copy()
        
        await self.app(scope, request.receive, send_wrapper)
        
        # Retornar um objeto response-like para compatibilidade
        class ResponseInfo:
            def __init__(self, status_code):
                self.status_code = status_code
        
        return ResponseInfo(status_code)

def setup_sentry_middleware(app):
    """
    Configura o middleware do Sentry na aplicação FastAPI
    
    Args:
        app: Instância da aplicação FastAPI
    """
    app.add_middleware(SentryMiddleware)
    logger.info("✅ Sentry middleware configured")

# Decorator para monitorar endpoints específicos
def monitor_endpoint(endpoint_name: str = None):
    """
    Decorator para monitorar endpoints específicos com mais detalhes
    
    Args:
        endpoint_name: Nome personalizado para o endpoint
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            name = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            with sentry_sdk.start_transaction(op="http", name=name):
                try:
                    add_breadcrumb(f"Starting endpoint: {name}", category="endpoint")
                    result = await func(*args, **kwargs)
                    add_breadcrumb(f"Endpoint completed: {name}", category="endpoint")
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context={"endpoint": name, "args": str(args)[:200]},
                        tags={"component": "endpoint", "endpoint_name": name}
                    )
                    raise
        
        return wrapper
    return decorator