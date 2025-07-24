"""
Aplicação principal do Backend Renum.

Este módulo inicializa a aplicação FastAPI, configura middlewares,
registra rotas e define eventos de inicialização e encerramento.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

from app.core.logger import logger
from app.core.config import get_settings
from app.db.database import get_db_instance
from app.core.middleware import AuthenticationMiddleware, RequestLoggingMiddleware
from app.api.routes import teams, team_executions, team_members


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de ciclo de vida da aplicação.
    
    Args:
        app: Aplicação FastAPI
    """
    # Inicialização
    logger.info("Starting Renum Backend application")
    
    # Inicializa o banco de dados
    db = get_db_instance()
    await db.client  # Inicializa o cliente
    
    # Inicializa o serviço de notificações
    from app.services.notification_service import notification_service
    from app.services.websocket_manager import websocket_manager
    
    # Conecta o serviço de notificações com o WebSocket manager
    notification_service.websocket_manager = websocket_manager
    await notification_service.initialize()
    
    yield
    
    # Encerramento
    logger.info("Shutting down Renum Backend application")
    
    # Finaliza o serviço de notificações
    await notification_service.shutdown()
    
    # Fecha a conexão com o banco de dados
    db = get_db_instance()
    await db.close()


# Cria a aplicação FastAPI
settings = get_settings()
app = FastAPI(
    title="Renum Backend API",
    description="""
    API for Renum Backend - Agent Teams Orchestration System
    
    This API allows you to create, manage, and execute teams of AI agents.
    Teams can be configured with different workflow strategies:
    
    * **Sequential**: Agents execute one after another in a defined order
    * **Parallel**: All agents execute simultaneously
    * **Pipeline**: Output of one agent becomes input for the next
    * **Conditional**: Execution flow depends on results of previous agents
    
    ## Authentication
    
    All endpoints require authentication using a JWT token.
    Include the token in the Authorization header:
    
    ```
    Authorization: Bearer YOUR_TOKEN
    ```
    
    ## Rate Limits
    
    * Maximum of 5 concurrent team executions per user
    * Maximum of 10 agents per team
    """,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Configura middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona middleware de autenticação
app.add_middleware(AuthenticationMiddleware)

# Adiciona middleware de logging
app.add_middleware(RequestLoggingMiddleware)


# Middleware de logging agora é implementado como uma classe separada


# Registra as rotas
app.include_router(
    teams.router, 
    prefix=f"{settings.API_PREFIX}",
    tags=["Teams Management"]
)
app.include_router(
    team_members.router, 
    prefix=f"{settings.API_PREFIX}",
    tags=["Team Members"]
)
app.include_router(
    team_executions.router, 
    prefix=f"{settings.API_PREFIX}",
    tags=["Team Executions"]
)

# Importa e registra as rotas WebSocket
from app.api.routes import websocket
app.include_router(
    websocket.router,
    prefix=f"{settings.API_PREFIX}",
    tags=["WebSocket"]
)

# Importa e registra as rotas WebSocket para canais e salas
from app.api.routes import websocket_channels
app.include_router(
    websocket_channels.router,
    prefix=f"{settings.API_PREFIX}",
    tags=["WebSocket Channels"]
)

# Importa e registra as rotas de notificações
# from app.api.routes import notifications
# app.include_router(
#     notifications.router,
#     prefix=f"{settings.API_PREFIX}",
#     tags=["Notifications"]
# )


@app.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da aplicação.
    
    Returns:
        Status da aplicação
    """
    return {"status": "ok", "version": settings.VERSION}


@app.get("/")
async def root():
    """
    Endpoint raiz da aplicação.
    
    Returns:
        Informações básicas sobre a API
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "API for Renum Backend - Agent Teams Orchestration System",
        "docs_url": "/docs"
    }