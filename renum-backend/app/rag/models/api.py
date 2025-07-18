"""
API models for the RAG module.

This module contains Pydantic models for request and response objects
used in the RAG module API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, UUID4, HttpUrl


class KnowledgeBaseCreate(BaseModel):
    """Request model for creating a knowledge base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    client_id: str


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base."""
    id: UUID4
    name: str
    description: Optional[str] = None
    client_id: str
    created_at: datetime
    updated_at: datetime
    collection_count: int = 0
    document_count: int = 0
    total_chunks: int = 0

    @classmethod
    def from_entity(cls, entity):
        """Create a response model from an entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            client_id=entity.client_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            collection_count=getattr(entity, 'collection_count', 0),
            document_count=getattr(entity, 'document_count', 0),
            total_chunks=getattr(entity, 'total_chunks', 0)
        )


class KnowledgeBaseUpdate(BaseModel):
    """Request model for updating a knowledge base."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class CollectionCreate(BaseModel):
    """Request model for creating a collection."""
    knowledge_base_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    """Response model for collection."""
    id: UUID4
    knowledge_base_id: UUID4
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    @classmethod
    def from_entity(cls, entity):
        """Create a response model from an entity."""
        return cls(
            id=entity.id,
            knowledge_base_id=entity.knowledge_base_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            document_count=getattr(entity, 'document_count', 0)
        )


class CollectionUpdate(BaseModel):
    """Request model for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response model for document."""
    id: UUID4
    collection_id: UUID4
    name: str
    description: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0
    version_count: int = 0

    @classmethod
    def from_entity(cls, entity):
        """Create a response model from an entity."""
        return cls(
            id=entity.id,
            collection_id=entity.collection_id,
            name=entity.name,
            description=entity.description,
            source_type=entity.source_type,
            source_url=entity.source_url,
            file_type=entity.file_type,
            file_size=entity.file_size,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            chunk_count=getattr(entity, 'chunk_count', 0),
            version_count=getattr(entity, 'version_count', 0)
        )


class ProcessingJobResponse(BaseModel):
    """Response model for processing job."""
    id: str
    document_id: str
    status: str
    progress: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RetrievalRequest(BaseModel):
    """Request model for retrieving chunks."""
    query: str
    collection_ids: List[str]
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None


class RetrievalResponse(BaseModel):
    """Response model for retrieval results."""
    chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]