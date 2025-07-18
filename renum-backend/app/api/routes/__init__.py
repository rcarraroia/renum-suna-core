"""
Módulo que contém as rotas da API.

Este módulo exporta os routers disponíveis na API.
"""

from fastapi import APIRouter

from app.api.routes import agent, rag, auth, suna_proxy

# Criar router principal
api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router)
api_router.include_router(agent.router)
api_router.include_router(rag.router)
api_router.include_router(suna_proxy.router)

__all__ = ["api_router"]