"""
Collection repository for the RAG module.

This module provides data access functions for knowledge collections.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from services.supabase import DBConnection
from knowledge_base.rag.models.entities import KnowledgeCollection


class CollectionRepository:
    """Repository for collection operations."""

    def __init__(self, db_connection: DBConnection = None):
        """Initialize the collection repository.
        
        Args:
            db_connection: Database connection.
        """
        self.db = db_connection or DBConnection()

    async def create(
        self, knowledge_base_id: str, name: str, description: Optional[str]
    ) -> KnowledgeCollection:
        """Create a new collection.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            name: Name of the collection.
            description: Description of the collection.
            
        Returns:
            Created collection.
        """
        client = await self.db.client
        
        collection_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        collection_data = {
            'id': collection_id,
            'knowledge_base_id': knowledge_base_id,
            'name': name,
            'description': description,
            'created_at': now,
            'updated_at': now
        }
        
        await client.table('knowledge_collections').insert(collection_data).execute()
        
        return KnowledgeCollection(
            id=collection_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            description=description,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )

    async def get_by_id(self, collection_id: str) -> Optional[KnowledgeCollection]:
        """Get a collection by ID.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            Collection or None if not found.
        """
        client = await self.db.client
        
        result = await client.table('knowledge_collections').select(
            'id', 'knowledge_base_id', 'name', 'description', 'created_at', 'updated_at'
        ).eq('id', collection_id).single().execute()
        
        if not result.data:
            return None
        
        return KnowledgeCollection(
            id=result.data['id'],
            knowledge_base_id=result.data['knowledge_base_id'],
            name=result.data['name'],
            description=result.data['description'],
            created_at=datetime.fromisoformat(result.data['created_at']),
            updated_at=datetime.fromisoformat(result.data['updated_at'])
        )

    async def get_by_knowledge_base_id(self, knowledge_base_id: str) -> List[KnowledgeCollection]:
        """Get all collections for a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            List of collections.
        """
        client = await self.db.client
        
        result = await client.table('knowledge_collections').select(
            'id', 'knowledge_base_id', 'name', 'description', 'created_at', 'updated_at'
        ).eq('knowledge_base_id', knowledge_base_id).order('created_at').execute()
        
        if not result.data:
            return []
        
        return [
            KnowledgeCollection(
                id=item['id'],
                knowledge_base_id=item['knowledge_base_id'],
                name=item['name'],
                description=item['description'],
                created_at=datetime.fromisoformat(item['created_at']),
                updated_at=datetime.fromisoformat(item['updated_at'])
            )
            for item in result.data
        ]

    async def update(
        self, collection_id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[KnowledgeCollection]:
        """Update a collection.
        
        Args:
            collection_id: ID of the collection.
            name: New name (optional).
            description: New description (optional).
            
        Returns:
            Updated collection or None if not found.
        """
        client = await self.db.client
        
        # Check if collection exists
        existing = await self.get_by_id(collection_id)
        if not existing:
            return None
        
        # Prepare update data
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        
        # Update collection
        await client.table('knowledge_collections').update(update_data).eq('id', collection_id).execute()
        
        # Get updated collection
        return await self.get_by_id(collection_id)

    async def delete(self, collection_id: str) -> bool:
        """Delete a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            True if deleted, False if not found.
        """
        client = await self.db.client
        
        # Check if collection exists
        existing = await self.get_by_id(collection_id)
        if not existing:
            return False
        
        # Get all documents in this collection
        documents_result = await client.table('documents').select(
            'id'
        ).eq('collection_id', collection_id).execute()
        
        document_ids = [item['id'] for item in documents_result.data]
        
        # Delete all chunks for these documents
        for document_id in document_ids:
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
        
        # Delete documents
        await client.table('documents').delete().eq('collection_id', collection_id).execute()
        
        # Delete collection
        await client.table('knowledge_collections').delete().eq('id', collection_id).execute()
        
        return True

    async def get_stats(self, collection_id: str) -> Dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            Statistics for the collection.
        """
        client = await self.db.client
        
        # Get document count
        documents_result = await client.rpc(
            'count_documents_in_collection',
            {'p_collection_id': collection_id}
        ).execute()
        
        document_count = documents_result.data[0]['count'] if documents_result.data else 0
        
        # Get chunk count
        chunks_result = await client.rpc(
            'count_chunks_in_collection',
            {'p_collection_id': collection_id}
        ).execute()
        
        chunk_count = chunks_result.data[0]['count'] if chunks_result.data else 0
        
        return {
            'document_count': document_count,
            'chunk_count': chunk_count
        }