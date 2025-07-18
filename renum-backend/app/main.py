"""
Main application module for the Renum backend.

This module initializes the FastAPI application and includes all routers.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.logger import logger
from app.core.config import get_settings
from app.core.database import initialize_db
from app.rag.utils.db_init import initialize_database as initialize_rag_db
from app.rag.api import router as old_rag_router
from app.api.routes import rag_router as new_rag_router
from app.api.routes import suna_router
from app.api.routes import auth_router
from app.api.routes import proxy_router
from app.api.routes.agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup
    logger.info("Starting Renum backend application")
    
    # Initialize database
    await initialize_db()
    
    # Initialize RAG database
    await initialize_rag_db()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Renum backend application")


# Create FastAPI application
app = FastAPI(
    title="Renum Platform API",
    description="API for the Renum Platform",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(old_rag_router, prefix="/api/v1")
app.include_router(new_rag_router, prefix="/api/v2/rag")
app.include_router(suna_router, prefix="/api/v2/suna")
app.include_router(auth_router, prefix="/api/v2/auth")
app.include_router(proxy_router, prefix="/api/v2/proxy")
app.include_router(agent_router, prefix="/api/v2/agents")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}