"""
Entity models for the RAG module.

This module contains Pydantic models that represent the database entities
used in the RAG module.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, UUID4


class KnowledgeBase(BaseModel):
    """Knowledge base entity."""
    id: UUID4
    name: str
    description: Optional[str] = None
    client_id: UUID4
    created_at: datetime
    updated_at: datetime


class KnowledgeCollection(BaseModel):
    """Knowledge collection entity."""
    id: UUID4
    knowledge_base_id: UUID4
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Document(BaseModel):
    """Document entity."""
    id: UUID4
    collection_id: UUID4
    name: str
    source_type: str  # file, url, text
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str  # processing, completed, failed
    created_at: datetime
    updated_at: datetime


class DocumentChunk(BaseModel):
    """Document chunk entity."""
    id: UUID4
    document_id: UUID4
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_id: Optional[str] = None
    created_at: datetime


class DocumentVersion(BaseModel):
    """Document version entity."""
    id: UUID4
    document_id: UUID4
    version_number: int
    change_type: str  # create, update, delete
    changed_by: UUID4
    change_description: Optional[str] = None
    created_at: datetime


class RetrievalFeedback(BaseModel):
    """Retrieval feedback entity."""
    id: UUID4
    thread_id: UUID4
    message_id: UUID4
    chunk_id: UUID4
    relevance_score: int
    user_id: UUID4
    feedback_text: Optional[str] = None
    created_at: datetime


class DocumentUsageStat(BaseModel):
    """Document usage statistics entity."""
    id: UUID4
    document_id: UUID4
    chunk_id: Optional[UUID4] = None
    agent_id: UUID4
    client_id: UUID4
    usage_count: int
    last_used_at: datetime
    first_used_at: datetime


class ClientPlan(BaseModel):
    """Client plan entity."""
    id: UUID4
    client_id: UUID4
    plan_type: str  # free, basic, premium, enterprise
    max_documents: int
    max_storage_mb: int
    max_queries_per_day: int
    current_usage: Dict[str, Any]
    plan_start_date: datetime
    plan_end_date: Optional[datetime] = None