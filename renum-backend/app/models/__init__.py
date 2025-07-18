"""
Pacote de modelos de dados para a Plataforma Renum.

Este pacote contém as classes que representam as entidades do sistema.
"""

from app.models.base import RenumBaseModel, Entity, TimestampedEntity
from app.models.rag import (
    KnowledgeBase,
    KnowledgeCollection,
    Document,
    DocumentChunk,
    DocumentVersion,
    DocumentUsageStats,
    RetrievalFeedback,
    ProcessingJob
)
from app.models.auth import (
    UserRole,
    ClientStatus,
    Client,
    User,
    Session,
    PasswordResetToken
)
from app.models.agent import (
    AgentStatus,
    AgentExecutionStatus,
    Agent,
    AgentExecution
)

__all__ = [
    # Base
    "RenumBaseModel",
    "Entity",
    "TimestampedEntity",
    
    # RAG
    "KnowledgeBase",
    "KnowledgeCollection",
    "Document",
    "DocumentChunk",
    "DocumentVersion",
    "DocumentUsageStats",
    "RetrievalFeedback",
    "ProcessingJob",
    
    # Auth
    "UserRole",
    "ClientStatus",
    "Client",
    "User",
    "Session",
    "PasswordResetToken",
    
    # Agent
    "AgentStatus",
    "AgentExecutionStatus",
    "Agent",
    "AgentExecution"
]