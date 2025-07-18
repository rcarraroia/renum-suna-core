"""
Entity models for the RAG module.

This module contains entity models for the RAG module.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID


class KnowledgeBase:
    """Knowledge base entity."""
    
    def __init__(
        self,
        id: UUID,
        name: str,
        client_id: str,
        description: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        collection_count: int = 0,
        document_count: int = 0,
        total_chunks: int = 0
    ):
        self.id = id
        self.name = name
        self.description = description
        self.client_id = client_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.collection_count = collection_count
        self.document_count = document_count
        self.total_chunks = total_chunks


class Collection:
    """Collection entity."""
    
    def __init__(
        self,
        id: UUID,
        knowledge_base_id: UUID,
        name: str,
        description: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        document_count: int = 0
    ):
        self.id = id
        self.knowledge_base_id = knowledge_base_id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.document_count = document_count


class Document:
    """Document entity."""
    
    def __init__(
        self,
        id: UUID,
        collection_id: UUID,
        name: str,
        source_type: str,
        status: str,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        chunk_count: int = 0,
        version_count: int = 0
    ):
        self.id = id
        self.collection_id = collection_id
        self.name = name
        self.description = description
        self.source_type = source_type
        self.source_url = source_url
        self.file_type = file_type
        self.file_size = file_size
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.chunk_count = chunk_count
        self.version_count = version_count


class DocumentChunk:
    """Document chunk entity."""
    
    def __init__(
        self,
        id: UUID,
        document_id: UUID,
        content: str,
        chunk_index: int,
        metadata: Dict[str, Any] = None,
        embedding_id: Optional[str] = None,
        created_at: datetime = None
    ):
        self.id = id
        self.document_id = document_id
        self.content = content
        self.chunk_index = chunk_index
        self.metadata = metadata or {}
        self.embedding_id = embedding_id
        self.created_at = created_at or datetime.now()


class ProcessingJob:
    """Processing job entity."""
    
    def __init__(
        self,
        id: UUID,
        document_id: UUID,
        status: str,
        progress: float,
        error_message: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id
        self.document_id = document_id
        self.status = status
        self.progress = progress
        self.error_message = error_message
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()


class RetrievalFeedback:
    """Retrieval feedback entity."""
    
    def __init__(
        self,
        id: UUID,
        thread_id: UUID,
        message_id: UUID,
        chunk_id: UUID,
        relevance_score: int,
        user_id: Optional[UUID] = None,
        feedback_text: Optional[str] = None,
        created_at: datetime = None
    ):
        self.id = id
        self.thread_id = thread_id
        self.message_id = message_id
        self.chunk_id = chunk_id
        self.relevance_score = relevance_score
        self.user_id = user_id
        self.feedback_text = feedback_text
        self.created_at = created_at or datetime.now()