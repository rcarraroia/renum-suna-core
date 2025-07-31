"""
Utilitários para facilitar o uso do Sentry no projeto
"""

import sentry_sdk
from typing import Dict, Any, Optional
import functools
import traceback
from utils.logger import logger

def capture_exception_with_context(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    level: str = "error"
):
    """
    Captura uma exceção com contexto adicional
    
    Args:
        exception: A exceção a ser capturada
        context: Contexto adicional para debug
        tags: Tags para categorizar o erro
        level: Nível do erro (error, warning, info)
    """
    with sentry_sdk.push_scope() as scope:
        # Adicionar contexto
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        # Adicionar tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        # Definir nível
        scope.level = level
        
        # Capturar exceção
        sentry_sdk.capture_exception(exception)
        
        # Log local também
        logger.error(f"Exception captured by Sentry: {str(exception)}", 
                    extra={"context": context, "tags": tags})

def capture_message_with_context(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    level: str = "info"
):
    """
    Captura uma mensagem com contexto adicional
    
    Args:
        message: Mensagem a ser enviada
        context: Contexto adicional
        tags: Tags para categorizar
        level: Nível da mensagem
    """
    with sentry_sdk.push_scope() as scope:
        # Adicionar contexto
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        # Adicionar tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        # Definir nível
        scope.level = level
        
        # Capturar mensagem
        sentry_sdk.capture_message(message, level=level)

def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
):
    """
    Adiciona um breadcrumb para rastreamento
    
    Args:
        message: Mensagem do breadcrumb
        category: Categoria (http, db, auth, etc.)
        level: Nível (info, warning, error)
        data: Dados adicionais
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )

def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Define contexto do usuário para o Sentry
    
    Args:
        user_id: ID do usuário
        email: Email do usuário (opcional)
        username: Nome do usuário (opcional)
    """
    user_data = {"id": user_id}
    
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    
    sentry_sdk.set_user(user_data)

def set_request_context(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None
):
    """
    Define contexto da requisição
    
    Args:
        method: Método HTTP
        url: URL da requisição
        headers: Headers da requisição
        query_params: Parâmetros de query
    """
    request_data = {
        "method": method,
        "url": url
    }
    
    if headers:
        # Filtrar headers sensíveis
        safe_headers = {k: v for k, v in headers.items() 
                       if k.lower() not in ['authorization', 'cookie', 'x-api-key']}
        request_data["headers"] = safe_headers
    
    if query_params:
        request_data["query_string"] = query_params
    
    sentry_sdk.set_context("request", request_data)

def monitor_performance(operation_name: str):
    """
    Decorator para monitorar performance de operações
    
    Args:
        operation_name: Nome da operação para identificação
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op="function", name=operation_name):
                try:
                    add_breadcrumb(f"Starting {operation_name}", category="performance")
                    result = await func(*args, **kwargs)
                    add_breadcrumb(f"Completed {operation_name}", category="performance")
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context={"operation": operation_name, "args": str(args)[:200]},
                        tags={"operation_type": "async_function"}
                    )
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op="function", name=operation_name):
                try:
                    add_breadcrumb(f"Starting {operation_name}", category="performance")
                    result = func(*args, **kwargs)
                    add_breadcrumb(f"Completed {operation_name}", category="performance")
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context={"operation": operation_name, "args": str(args)[:200]},
                        tags={"operation_type": "sync_function"}
                    )
                    raise
        
        # Retornar wrapper apropriado baseado na função
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def monitor_database_operation(operation_type: str, table: Optional[str] = None):
    """
    Decorator específico para operações de banco de dados
    
    Args:
        operation_type: Tipo da operação (select, insert, update, delete)
        table: Nome da tabela (opcional)
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_name = f"db.{operation_type}"
            if table:
                operation_name += f".{table}"
            
            with sentry_sdk.start_span(op="db", description=operation_name):
                try:
                    add_breadcrumb(
                        f"Database {operation_type} on {table or 'unknown'}",
                        category="db"
                    )
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context={
                            "operation_type": operation_type,
                            "table": table,
                            "function": func.__name__
                        },
                        tags={"component": "database"}
                    )
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_name = f"db.{operation_type}"
            if table:
                operation_name += f".{table}"
            
            with sentry_sdk.start_span(op="db", description=operation_name):
                try:
                    add_breadcrumb(
                        f"Database {operation_type} on {table or 'unknown'}",
                        category="db"
                    )
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context={
                            "operation_type": operation_type,
                            "table": table,
                            "function": func.__name__
                        },
                        tags={"component": "database"}
                    )
                    raise
        
        # Retornar wrapper apropriado
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def monitor_agent_execution(agent_id: Optional[str] = None, thread_id: Optional[str] = None):
    """
    Decorator para monitorar execuções de agentes
    
    Args:
        agent_id: ID do agente
        thread_id: ID da thread
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            operation_name = "agent.execution"
            
            with sentry_sdk.start_transaction(op="agent", name=operation_name):
                # Configurar contexto
                context = {"component": "agent"}
                if agent_id:
                    context["agent_id"] = agent_id
                if thread_id:
                    context["thread_id"] = thread_id
                
                sentry_sdk.set_context("agent_execution", context)
                
                try:
                    add_breadcrumb("Starting agent execution", category="agent")
                    result = await func(*args, **kwargs)
                    add_breadcrumb("Agent execution completed", category="agent")
                    return result
                except Exception as e:
                    capture_exception_with_context(
                        e,
                        context=context,
                        tags={"component": "agent", "operation": "execution"}
                    )
                    raise
        
        return wrapper
    return decorator

class SentryContextManager:
    """
    Context manager para facilitar o uso de contexto do Sentry
    """
    
    def __init__(self, operation_name: str, **context):
        self.operation_name = operation_name
        self.context = context
        self.transaction = None
    
    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(
            op="custom", 
            name=self.operation_name
        )
        self.transaction.__enter__()
        
        # Adicionar contexto
        for key, value in self.context.items():
            sentry_sdk.set_context(key, value)
        
        add_breadcrumb(f"Starting {self.operation_name}", category="custom")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            capture_exception_with_context(
                exc_val,
                context=self.context,
                tags={"operation": self.operation_name}
            )
        else:
            add_breadcrumb(f"Completed {self.operation_name}", category="custom")
        
        if self.transaction:
            self.transaction.__exit__(exc_type, exc_val, exc_tb)

# Funções de conveniência
def with_sentry_context(operation_name: str, **context):
    """
    Função de conveniência para criar um context manager do Sentry
    
    Usage:
        with with_sentry_context("user_registration", user_id="123"):
            # código aqui
    """
    return SentryContextManager(operation_name, **context)