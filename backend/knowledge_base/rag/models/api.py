"""
API models for the RAG module.

This module contains Pydantic models for request and response objects
used in the RAG module API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, UUID4, HttpUrl


class CreateKnowledgeBaseRequest(BaseModel):
    """Request model for creating a knowledge base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base."""
    id: UUID4
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    collection_count: int = 0
    document_count: int = 0
    total_chunks: int = 0


class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""
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


class UploadDocumentRequest(BaseModel):
    """Request model for uploading a document."""
    name: Optional[str] = None  # If not provided, will use filename
    description: Optional[str] = None


class AddUrlRequest(BaseModel):
    """Request model for adding a URL."""
    url: HttpUrl
    name: Optional[str] = None  # If not provided, will use URL title
    description: Optional[str] = None


class AddTextRequest(BaseModel):
    """Request model for adding text."""
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
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


class ChunkResponse(BaseModel):
    """Response model for document chunk."""
    id: UUID4
    document_id: UUID4
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    created_at: datetime


class ProcessingJobResponse(BaseModel):
    """Response model for processing job."""
    job_id: UUID4
    document_id: UUID4
    status: str
    progress: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RetrieveRequest(BaseModel):
    """Request model for retrieving chunks."""
    query: str
    collection_ids: Optional[List[UUID4]] = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None


class RetrieveResponse(BaseModel):
    """Response model for retrieval results."""
    chunks: List[ChunkResponse]
    query: str
    total_chunks: int


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    message_id: UUID4
    chunk_id: UUID4
    relevance_score: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None


class UsageStatResponse(BaseModel):
    """Response model for usage statistics."""
    document_id: UUID4
    document_name: str
    usage_count: int
    last_used_at: datetime
    first_used_at: datetime