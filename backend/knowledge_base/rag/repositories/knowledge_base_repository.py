"""
Knowledge base repository for the RAG module.

This module provides data access functions for knowledge bases.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from services.supabase import DBConnection
from knowledge_base.rag.models.entities import KnowledgeBase


class KnowledgeBaseRepository:
    """Repository for knowledge base operations."""

    def __init__(self, db_connection: DBConnection = None):
        """Initialize the knowledge base repository.
        
        Args:
            db_connection: Database connection.
        """
        self.db = db_connection or DBConnection()

    async def create(
        self, name: str, description: Optional[str], client_id: str
    ) -> KnowledgeBase:
        """Create a new knowledge base.
        
        Args:
            name: Name of the knowledge base.
            description: Description of the knowledge base.
            client_id: ID of the client.
            
        Returns:
            Created knowledge base.
        """
        client = await self.db.client
        
        knowledge_base_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        knowledge_base_data = {
            'id': knowledge_base_id,
            'name': name,
            'description': description,
            'client_id': client_id,
            'created_at': now,
            'updated_at': now
        }
        
        await client.table('knowledge_bases').insert(knowledge_base_data).execute()
        
        return KnowledgeBase(
            id=knowledge_base_id,
            name=name,
            description=description,
            client_id=client_id,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )

    async def get_by_id(self, knowledge_base_id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Knowledge base or None if not found.
        """
        client = await self.db.client
        
        result = await client.table('knowledge_bases').select(
            'id', 'name', 'description', 'client_id', 'created_at', 'updated_at'
        ).eq('id', knowledge_base_id).single().execute()
        
        if not result.data:
            return None
        
        return KnowledgeBase(
            id=result.data['id'],
            name=result.data['name'],
            description=result.data['description'],
            client_id=result.data['client_id'],
            created_at=datetime.fromisoformat(result.data['created_at']),
            updated_at=datetime.fromisoformat(result.data['updated_at'])
        )

    async def get_by_client_id(self, client_id: str) -> List[KnowledgeBase]:
        """Get all knowledge bases for a client.
        
        Args:
            client_id: ID of the client.
            
        Returns:
            List of knowledge bases.
        """
        client = await self.db.client
        
        result = await client.table('knowledge_bases').select(
            'id', 'name', 'description', 'client_id', 'created_at', 'updated_at'
        ).eq('client_id', client_id).order('created_at').execute()
        
        if not result.data:
            return []
        
        return [
            KnowledgeBase(
                id=item['id'],
                name=item['name'],
                description=item['description'],
                client_id=item['client_id'],
                created_at=datetime.fromisoformat(item['created_at']),
                updated_at=datetime.fromisoformat(item['updated_at'])
            )
            for item in result.data
        ]

    async def update(
        self, knowledge_base_id: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[KnowledgeBase]:
        """Update a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            name: New name (optional).
            description: New description (optional).
            
        Returns:
            Updated knowledge base or None if not found.
        """
        client = await self.db.client
        
        # Check if knowledge base exists
        existing = await self.get_by_id(knowledge_base_id)
        if not existing:
            return None
        
        # Prepare update data
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        
        # Update knowledge base
        await client.table('knowledge_bases').update(update_data).eq('id', knowledge_base_id).execute()
        
        # Get updated knowledge base
        return await self.get_by_id(knowledge_base_id)

    async def delete(self, knowledge_base_id: str) -> bool:
        """Delete a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            True if deleted, False if not found.
        """
        client = await self.db.client
        
        # Check if knowledge base exists
        existing = await self.get_by_id(knowledge_base_id)
        if not existing:
            return False
        
        # Get all collections for this knowledge base
        collections_result = await client.table('knowledge_collections').select(
            'id'
        ).eq('knowledge_base_id', knowledge_base_id).execute()
        
        collection_ids = [item['id'] for item in collections_result.data]
        
        # Delete all documents in these collections
        for collection_id in collection_ids:
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
        
        # Delete collections
        await client.table('knowledge_collections').delete().eq('knowledge_base_id', knowledge_base_id).execute()
        
        # Delete knowledge base
        await client.table('knowledge_bases').delete().eq('id', knowledge_base_id).execute()
        
        return True

    async def get_stats(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Get statistics for a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Statistics for the knowledge base.
        """
        client = await self.db.client
        
        # Get collection count
        collections_result = await client.rpc(
            'count_collections_in_kb',
            {'p_knowledge_base_id': knowledge_base_id}
        ).execute()
        
        collection_count = collections_result.data[0]['count'] if collections_result.data else 0
        
        # Get document count
        documents_result = await client.rpc(
            'count_documents_in_kb',
            {'p_knowledge_base_id': knowledge_base_id}
        ).execute()
        
        document_count = documents_result.data[0]['count'] if documents_result.data else 0
        
        # Get chunk count
        chunks_result = await client.rpc(
            'count_chunks_in_kb',
            {'p_knowledge_base_id': knowledge_base_id}
        ).execute()
        
        chunk_count = chunks_result.data[0]['count'] if chunks_result.data else 0
        
        return {
            'collection_count': collection_count,
            'document_count': document_count,
            'chunk_count': chunk_count
        }