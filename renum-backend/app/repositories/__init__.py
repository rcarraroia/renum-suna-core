"""
Pacote de repositórios para a Plataforma Renum.

Este pacote contém as implementações do padrão Repository para acesso ao banco de dados.
"""

from app.repositories.base import Repository, SupabaseRepository, PaginatedResult
from app.repositories.rag import (
    KnowledgeBaseRepository,
    KnowledgeCollectionRepository,
    DocumentRepository,
    DocumentChunkRepository,
    knowledge_base_repository,
    knowledge_collection_repository,
    document_repository,
    document_chunk_repository
)
from app.repositories.auth import (
    ClientRepository,
    UserRepository,
    SessionRepository,
    PasswordResetTokenRepository,
    client_repository,
    user_repository,
    session_repository,
    password_reset_token_repository
)
from app.repositories.agent import (
    AgentRepository,
    AgentExecutionRepository,
    agent_repository,
    agent_execution_repository
)

__all__ = [
    # Base
    "Repository",
    "SupabaseRepository",
    "PaginatedResult",
    
    # RAG
    "KnowledgeBaseRepository",
    "KnowledgeCollectionRepository",
    "DocumentRepository",
    "DocumentChunkRepository",
    "knowledge_base_repository",
    "knowledge_collection_repository",
    "document_repository",
    "document_chunk_repository",
    
    # Auth
    "ClientRepository",
    "UserRepository",
    "SessionRepository",
    "PasswordResetTokenRepository",
    "client_repository",
    "user_repository",
    "session_repository",
    "password_reset_token_repository",
    
    # Agent
    "AgentRepository",
    "AgentExecutionRepository",
    "agent_repository",
    "agent_execution_repository"
]