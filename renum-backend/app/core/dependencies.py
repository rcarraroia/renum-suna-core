"""
Dependências para injeção de dependência no FastAPI.

Este módulo define as dependências que podem ser injetadas nos endpoints da API,
como repositórios, serviços e clientes.
"""

try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
from fastapi import Depends

from app.db.database import get_db
# from app.repositories.team_repository import TeamRepository
# from app.repositories.team_execution_repository import TeamExecutionRepository
from app.services.suna_api_client import SunaApiClient
from app.services.team_context_manager import TeamContextManager
from app.services.team_message_bus import TeamMessageBus
from app.services.api_key_manager import ApiKeyManager
from app.services.execution_engine import ExecutionEngine
from app.services.team_orchestrator import TeamOrchestrator
from app.services.websocket_manager import websocket_manager
from app.core.config import get_settings


# Redis client
async def get_redis_client():
    """
    Obtém o cliente Redis.
    
    Returns:
        Cliente Redis
    """
    if not REDIS_AVAILABLE:
        # Mock Redis client para desenvolvimento
        class MockRedis:
            async def get(self, key): return None
            async def set(self, key, value, ex=None): return True
            async def delete(self, key): return True
            async def close(self): pass
        
        yield MockRedis()
        return
    
    settings = get_settings()
    redis = await aioredis.from_url(settings.REDIS_URL)
    try:
        yield redis
    finally:
        await redis.close()


# Suna API client
async def get_suna_client():
    """
    Obtém o cliente da API do Suna Core.
    
    Returns:
        Cliente da API do Suna Core
    """
    settings = get_settings()
    client = SunaApiClient(settings.SUNA_API_URL, settings.SUNA_API_KEY)
    await client.initialize()
    try:
        yield client
    finally:
        await client.close()


# Team repository
async def get_team_repository():
    """
    Obtém o repositório de equipes.
    
    Returns:
        Repositório de equipes
    """
    # Temporariamente desabilitado para testes
    return None  # TeamRepository()


# Team execution repository
async def get_team_execution_repository():
    """
    Obtém o repositório de execuções de equipe.
    
    Returns:
        Repositório de execuções de equipe
    """
    # Temporariamente desabilitado para testes
    return None  # TeamExecutionRepository()


# API key manager
async def get_api_key_manager(db=Depends(get_db)):
    """
    Obtém o gerenciador de API keys.
    
    Args:
        db: Conexão com o banco de dados
        
    Returns:
        Gerenciador de API keys
    """
    return ApiKeyManager(db)


# Team context manager
async def get_team_context_manager(redis=Depends(get_redis_client)):
    """
    Obtém o gerenciador de contexto compartilhado.
    
    Args:
        redis: Cliente Redis
        
    Returns:
        Gerenciador de contexto compartilhado
    """
    return TeamContextManager(redis)


# Team message bus
async def get_team_message_bus(redis=Depends(get_redis_client)):
    """
    Obtém o sistema de mensagens entre agentes.
    
    Args:
        redis: Cliente Redis
        
    Returns:
        Sistema de mensagens entre agentes
    """
    return TeamMessageBus(redis)


# Execution engine
async def get_execution_engine(
    execution_repository=Depends(get_team_execution_repository),
    suna_client=Depends(get_suna_client),
    context_manager=Depends(get_team_context_manager),
    message_bus=Depends(get_team_message_bus),
    api_key_manager=Depends(get_api_key_manager)
):
    """
    Obtém o motor de execução.
    
    Args:
        execution_repository: Repositório de execuções
        suna_client: Cliente da API do Suna Core
        context_manager: Gerenciador de contexto compartilhado
        message_bus: Sistema de mensagens entre agentes
        api_key_manager: Gerenciador de API keys
        
    Returns:
        Motor de execução
    """
    return ExecutionEngine(
        execution_repository,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )


# Team orchestrator
async def get_team_orchestrator(
    team_repository=Depends(get_team_repository),
    execution_repository=Depends(get_team_execution_repository),
    execution_engine=Depends(get_execution_engine),
    suna_client=Depends(get_suna_client),
    context_manager=Depends(get_team_context_manager),
    message_bus=Depends(get_team_message_bus),
    api_key_manager=Depends(get_api_key_manager)
):
    """
    Obtém o orquestrador de equipes.
    
    Args:
        team_repository: Repositório de equipes
        execution_repository: Repositório de execuções
        execution_engine: Motor de execução
        suna_client: Cliente da API do Suna Core
        context_manager: Gerenciador de contexto compartilhado
        message_bus: Sistema de mensagens entre agentes
        api_key_manager: Gerenciador de API keys
        
    Returns:
        Orquestrador de equipes
    """
    return TeamOrchestrator(
        team_repository,
        execution_repository,
        execution_engine,
        suna_client,
        context_manager,
        message_bus,
        api_key_manager
    )


# WebSocket repository
async def get_websocket_repository(redis=Depends(get_redis_client)):
    """
    Obtém o repositório de WebSocket.
    
    Args:
        redis: Cliente Redis
        
    Returns:
        Repositório de WebSocket
    """
    from app.repositories.websocket_repository import WebSocketRepository
    return WebSocketRepository(redis)


# WebSocket manager
async def get_websocket_manager(
    redis=Depends(get_redis_client),
    repository=Depends(get_websocket_repository)
):
    """
    Obtém o gerenciador de WebSockets.
    
    Args:
        redis: Cliente Redis para PubSub
        repository: Repositório de WebSocket
        
    Returns:
        Gerenciador de WebSockets
    """
    # Configura a instância global com o cliente Redis e o repositório
    websocket_manager.redis = redis
    websocket_manager.set_repository(repository)
    return websocket_manager


# Thread manager integration
async def get_thread_manager_integration(
    context_manager=Depends(get_team_context_manager),
    message_bus=Depends(get_team_message_bus)
):
    """
    Obtém a integração com o ThreadManager.
    
    Args:
        context_manager: Gerenciador de contexto compartilhado
        message_bus: Sistema de mensagens entre agentes
        
    Returns:
        Integração com o ThreadManager
    """
    from app.services.thread_manager_integration import TeamThreadManagerIntegration
    return TeamThreadManagerIntegration(context_manager, message_bus)


# Team context tool factory
def get_team_context_tool_factory(context_manager=Depends(get_team_context_manager)):
    """
    Obtém uma fábrica de ferramentas de contexto compartilhado.
    
    Args:
        context_manager: Gerenciador de contexto compartilhado
        
    Returns:
        Função para criar ferramentas de contexto compartilhado
    """
    from app.services.team_context_tool import TeamContextTool
    
    def create_tool(execution_id, agent_id):
        return TeamContextTool(context_manager, execution_id, agent_id)
    
    return create_tool


# Team message tool factory
def get_team_message_tool_factory(message_bus=Depends(get_team_message_bus)):
    """
    Obtém uma fábrica de ferramentas de mensagens da equipe.
    
    Args:
        message_bus: Sistema de mensagens entre agentes
        
    Returns:
        Função para criar ferramentas de mensagens da equipe
    """
    from app.services.team_message_tool import TeamMessageTool
    
    def create_tool(execution_id, agent_id):
        return TeamMessageTool(message_bus, execution_id, agent_id)
    
    return create_tool


# Billing manager
async def get_billing_manager(execution_repository=Depends(get_team_execution_repository)):
    """
    Obtém o gerenciador de billing.
    
    Args:
        execution_repository: Repositório de execuções
        
    Returns:
        Gerenciador de billing
    """
    from app.services.billing_manager import BillingManager
    return BillingManager(execution_repository)


# WebSocket channel service
async def get_websocket_channel_service(
    redis=Depends(get_redis_client),
    repository=Depends(get_websocket_repository)
):
    """
    Obtém o serviço de canais WebSocket.
    
    Args:
        redis: Cliente Redis
        repository: Repositório de WebSocket
        
    Returns:
        Serviço de canais WebSocket
    """
    from app.services.websocket_channel_service import websocket_channel_service
    websocket_channel_service.redis = redis
    websocket_channel_service.repository = repository
    return websocket_channel_service


# WebSocket resilience service
async def get_websocket_resilience_service(
    redis=Depends(get_redis_client),
    repository=Depends(get_websocket_repository)
):
    """
    Obtém o serviço de resiliência WebSocket.
    
    Args:
        redis: Cliente Redis
        repository: Repositório de WebSocket
        
    Returns:
        Serviço de resiliência WebSocket
    """
    from app.services.websocket_resilience_service import websocket_resilience_service
    websocket_resilience_service.redis = redis
    websocket_resilience_service.repository = repository
    await websocket_resilience_service.start_cleanup_task()
    return websocket_resilience_service