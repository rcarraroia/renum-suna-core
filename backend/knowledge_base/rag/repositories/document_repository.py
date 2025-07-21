"""
Document repository for the RAG module.

This module provides data access functions for documents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from services.supabase import DBConnection
from knowledge_base.rag.models.entities import Document, DocumentChunk, DocumentVersion


class DocumentRepository:
    """Repository for document operations."""

    def __init__(self, db_connection: DBConnection = None):
        """Initialize the document repository.
        
        Args:
            db_connection: Database connection.
        """
        self.db = db_connection or DBConnection()

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            Document or None if not found.
        """
        client = await self.db.client
        
        result = await client.table('documents').select(
            'id', 'collection_id', 'name', 'source_type', 'source_url',
            'file_type', 'file_size', 'status', 'created_at', 'updated_at'
        ).eq('id', document_id).single().execute()
        
        if not result.data:
            return None
        
        return Document(
            id=result.data['id'],
            collection_id=result.data['collection_id'],
            name=result.data['name'],
            source_type=result.data['source_type'],
            source_url=result.data['source_url'],
            file_type=result.data['file_type'],
            file_size=result.data['file_size'],
            status=result.data['status'],
            created_at=datetime.fromisoformat(result.data['created_at']),
            updated_at=datetime.fromisoformat(result.data['updated_at'])
        )

    async def get_by_collection_id(self, collection_id: str) -> List[Document]:
        """Get all documents in a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            List of documents.
        """
        client = await self.db.client
        
        result = await client.table('documents').select(
            'id', 'collection_id', 'name', 'source_type', 'source_url',
            'file_type', 'file_size', 'status', 'created_at', 'updated_at'
        ).eq('collection_id', collection_id).order('created_at').execute()
        
        if not result.data:
            return []
        
        return [
            Document(
                id=item['id'],
                collection_id=item['collection_id'],
                name=item['name'],
                source_type=item['source_type'],
                source_url=item['source_url'],
                file_type=item['file_type'],
                file_size=item['file_size'],
                status=item['status'],
                created_at=datetime.fromisoformat(item['created_at']),
                updated_at=datetime.fromisoformat(item['updated_at'])
            )
            for item in result.data
        ]

    async def update(
        self, document_id: str, name: Optional[str] = None, status: Optional[str] = None
    ) -> Optional[Document]:
        """Update a document.
        
        Args:
            document_id: ID of the document.
            name: New name (optional).
            status: New status (optional).
            
        Returns:
            Updated document or None if not found.
        """
        client = await self.db.client
        
        # Check if document exists
        existing = await self.get_by_id(document_id)
        if not existing:
            return None
        
        # Prepare update data
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        if name is not None:
            update_data['name'] = name
        if status is not None:
            update_data['status'] = status
        
        # Update document
        await client.table('documents').update(update_data).eq('id', document_id).execute()
        
        # Get updated document
        return await self.get_by_id(document_id)

    async def delete(self, document_id: str) -> bool:
        """Delete a document.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            True if deleted, False if not found.
        """
        client = await self.db.client
        
        # Check if document exists
        existing = await self.get_by_id(document_id)
        if not existing:
            return False
        
        # Get all chunks for this document
        chunks_result = await client.table('document_chunks').select(
            'id', 'embedding_id'
        ).eq('document_id', document_id).execute()
        
        # Delete embeddings
        embedding_ids = [
            item['embedding_id'] for item in chunks_result.data
            if item['embedding_id']
        ]
        
        if embedding_ids:
            await client.rpc(
                'delete_embeddings',
                {'p_embedding_ids': embedding_ids}
            ).execute()
        
        # Delete chunks
        await client.table('document_chunks').delete().eq('document_id', document_id).execute()
        
        # Delete document versions
        await client.table('document_versions').delete().eq('document_id', document_id).execute()
        
        # Delete document usage stats
        await client.table('document_usage_stats').delete().eq('document_id', document_id).execute()
        
        # Delete document
        await client.table('documents').delete().eq('id', document_id).execute()
        
        return True

    async def get_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            List of document chunks.
        """
        client = await self.db.client
        
        result = await client.table('document_chunks').select(
            'id', 'document_id', 'content', 'chunk_index',
            'metadata', 'embedding_id', 'created_at'
        ).eq('document_id', document_id).order('chunk_index').execute()
        
        if not result.data:
            return []
        
        return [
            DocumentChunk(
                id=item['id'],
                document_id=item['document_id'],
                content=item['content'],
                chunk_index=item['chunk_index'],
                metadata=item['metadata'],
                embedding_id=item['embedding_id'],
                created_at=datetime.fromisoformat(item['created_at'])
            )
            for item in result.data
        ]

    async def get_versions(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions for a document.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            List of document versions.
        """
        client = await self.db.client
        
        result = await client.table('document_versions').select(
            'id', 'document_id', 'version_number', 'change_type',
            'changed_by', 'change_description', 'created_at'
        ).eq('document_id', document_id).order('version_number').execute()
        
        if not result.data:
            return []
        
        return [
            DocumentVersion(
                id=item['id'],
                document_id=item['document_id'],
                version_number=item['version_number'],
                change_type=item['change_type'],
                changed_by=item['changed_by'],
                change_description=item['change_description'],
                created_at=datetime.fromisoformat(item['created_at'])
            )
            for item in result.data
        ]

    async def get_stats(self, document_id: str) -> Dict[str, Any]:
        """Get statistics for a document.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            Statistics for the document.
        """
        client = await self.db.client
        
        # Get chunk count
        chunks_result = await client.rpc(
            'count_chunks_in_document',
            {'p_document_id': document_id}
        ).execute()
        
        chunk_count = chunks_result.data[0]['count'] if chunks_result.data else 0
        
        # Get version count
        versions_result = await client.rpc(
            'count_versions_in_document',
            {'p_document_id': document_id}
        ).execute()
        
        version_count = versions_result.data[0]['count'] if versions_result.data else 0
        
        # Get usage stats
        usage_result = await client.rpc(
            'get_document_usage_stats',
            {'p_document_id': document_id}
        ).execute()
        
        usage_count = 0
        last_used_at = None
        
        if usage_result.data and usage_result.data[0]:
            usage_count = usage_result.data[0].get('usage_count', 0)
            last_used_at = usage_result.data[0].get('last_used_at')
        
        return {
            'chunk_count': chunk_count,
            'version_count': version_count,
            'usage_count': usage_count,
            'last_used_at': last_used_at
        }