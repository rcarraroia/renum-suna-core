"""
Collection repository for the RAG module.

This module provides functionality for managing collections.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logger import logger
from app.core.database import get_db_client


class CollectionRepository:
    """Repository for collections."""

    async def create(
        self,
        knowledge_base_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a collection.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            name: Name of the collection.
            description: Description of the collection.
            
        Returns:
            Created collection.
        """
        try:
            client = await get_db_client()
            
            now = datetime.utcnow()
            collection_data = {
                "id": str(uuid.uuid4()),
                "knowledge_base_id": knowledge_base_id,
                "name": name,
                "description": description,
                "created_at": now,
                "updated_at": now
            }
            
            result = await client.table("knowledge_collections").insert(collection_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create collection")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    async def get_by_id(self, collection_id: str) -> Dict[str, Any]:
        """Get a collection by ID.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            Collection.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("knowledge_collections").select("*").eq("id", collection_id).execute()
            
            if not result.data:
                raise ValueError(f"Collection not found: {collection_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error getting collection: {str(e)}")
            raise

    async def get_by_knowledge_base_id(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
        """Get collections by knowledge base ID.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            List of collections.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("knowledge_collections").select("*").eq("knowledge_base_id", knowledge_base_id).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting collections by knowledge base ID: {str(e)}")
            raise

    async def update(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a collection.
        
        Args:
            collection_id: ID of the collection.
            name: New name of the collection.
            description: New description of the collection.
            
        Returns:
            Updated collection.
        """
        try:
            client = await get_db_client()
            
            update_data = {"updated_at": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name
            
            if description is not None:
                update_data["description"] = description
            
            result = await client.table("knowledge_collections").update(update_data).eq("id", collection_id).execute()
            
            if not result.data:
                raise ValueError(f"Failed to update collection: {collection_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating collection: {str(e)}")
            raise

    async def delete(self, collection_id: str) -> bool:
        """Delete a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            True if the collection was deleted, False otherwise.
        """
        try:
            client = await get_db_client()
            
            # Get documents in the collection
            documents_result = await client.table("documents").select("id").eq("collection_id", collection_id).execute()
            
            # Delete documents and related data
            if documents_result.data:
                from app.rag.repositories.document_repository import DocumentRepository
                document_repository = DocumentRepository()
                
                for document in documents_result.data:
                    await document_repository.delete(document["id"])
            
            # Delete collection
            result = await client.table("knowledge_collections").delete().eq("id", collection_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise

    async def get_document_count(self, collection_id: str) -> int:
        """Get the number of documents in a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            Number of documents.
        """
        try:
            client = await get_db_client()
            
            result = await client.rpc(
                "count_documents_in_collection",
                {"p_collection_id": collection_id}
            ).execute()
            
            if not result.data:
                return 0
            
            return result.data[0]["count"]
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

    async def get_chunk_count(self, collection_id: str) -> int:
        """Get the number of chunks in a collection.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            Number of chunks.
        """
        try:
            client = await get_db_client()
            
            result = await client.rpc(
                "count_chunks_in_collection",
                {"p_collection_id": collection_id}
            ).execute()
            
            if not result.data:
                return 0
            
            return result.data[0]["count"]
        except Exception as e:
            logger.error(f"Error getting chunk count: {str(e)}")
            return 0