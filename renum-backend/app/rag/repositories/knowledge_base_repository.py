"""
Knowledge base repository for the RAG module.

This module provides functionality for managing knowledge bases.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logger import logger
from app.core.database import get_db_client


class KnowledgeBaseRepository:
    """Repository for knowledge bases."""

    async def create(
        self,
        name: str,
        client_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a knowledge base.
        
        Args:
            name: Name of the knowledge base.
            client_id: ID of the client.
            description: Description of the knowledge base.
            
        Returns:
            Created knowledge base.
        """
        try:
            client = await get_db_client()
            
            now = datetime.utcnow()
            kb_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "client_id": client_id,
                "description": description,
                "created_at": now,
                "updated_at": now
            }
            
            result = await client.table("knowledge_bases").insert(kb_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create knowledge base")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            raise

    async def get_by_id(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Get a knowledge base by ID.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Knowledge base.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("knowledge_bases").select("*").eq("id", knowledge_base_id).execute()
            
            if not result.data:
                raise ValueError(f"Knowledge base not found: {knowledge_base_id}")
            
            kb = result.data[0]
            
            # Get collection count
            collection_count = await self.get_collection_count(knowledge_base_id)
            kb["collection_count"] = collection_count
            
            # Get document count
            document_count = await self.get_document_count(knowledge_base_id)
            kb["document_count"] = document_count
            
            # Get chunk count
            chunk_count = await self.get_chunk_count(knowledge_base_id)
            kb["total_chunks"] = chunk_count
            
            return kb
        except Exception as e:
            logger.error(f"Error getting knowledge base: {str(e)}")
            raise

    async def get_by_client_id(self, client_id: str) -> List[Dict[str, Any]]:
        """Get knowledge bases by client ID.
        
        Args:
            client_id: ID of the client.
            
        Returns:
            List of knowledge bases.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("knowledge_bases").select("*").eq("client_id", client_id).execute()
            
            kbs = result.data or []
            
            # Get additional stats for each knowledge base
            for kb in kbs:
                # Get collection count
                collection_count = await self.get_collection_count(kb["id"])
                kb["collection_count"] = collection_count
                
                # Get document count
                document_count = await self.get_document_count(kb["id"])
                kb["document_count"] = document_count
                
                # Get chunk count
                chunk_count = await self.get_chunk_count(kb["id"])
                kb["total_chunks"] = chunk_count
            
            return kbs
        except Exception as e:
            logger.error(f"Error getting knowledge bases by client ID: {str(e)}")
            raise

    async def update(
        self,
        knowledge_base_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            name: New name of the knowledge base.
            description: New description of the knowledge base.
            
        Returns:
            Updated knowledge base.
        """
        try:
            client = await get_db_client()
            
            update_data = {"updated_at": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name
            
            if description is not None:
                update_data["description"] = description
            
            result = await client.table("knowledge_bases").update(update_data).eq("id", knowledge_base_id).execute()
            
            if not result.data:
                raise ValueError(f"Failed to update knowledge base: {knowledge_base_id}")
            
            kb = result.data[0]
            
            # Get collection count
            collection_count = await self.get_collection_count(knowledge_base_id)
            kb["collection_count"] = collection_count
            
            # Get document count
            document_count = await self.get_document_count(knowledge_base_id)
            kb["document_count"] = document_count
            
            # Get chunk count
            chunk_count = await self.get_chunk_count(knowledge_base_id)
            kb["total_chunks"] = chunk_count
            
            return kb
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            raise

    async def delete(self, knowledge_base_id: str) -> bool:
        """Delete a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            True if the knowledge base was deleted, False otherwise.
        """
        try:
            client = await get_db_client()
            
            # Get collections in the knowledge base
            collections_result = await client.table("knowledge_collections").select("id").eq("knowledge_base_id", knowledge_base_id).execute()
            
            # Delete collections and related data
            if collections_result.data:
                from app.rag.repositories.collection_repository import CollectionRepository
                collection_repository = CollectionRepository()
                
                for collection in collections_result.data:
                    await collection_repository.delete(collection["id"])
            
            # Delete knowledge base
            result = await client.table("knowledge_bases").delete().eq("id", knowledge_base_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting knowledge base: {str(e)}")
            raise

    async def get_collection_count(self, knowledge_base_id: str) -> int:
        """Get the number of collections in a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Number of collections.
        """
        try:
            client = await get_db_client()
            
            result = await client.rpc(
                "count_collections_in_kb",
                {"p_knowledge_base_id": knowledge_base_id}
            ).execute()
            
            if not result.data:
                return 0
            
            return result.data[0]["count"]
        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0

    async def get_document_count(self, knowledge_base_id: str) -> int:
        """Get the number of documents in a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Number of documents.
        """
        try:
            client = await get_db_client()
            
            result = await client.rpc(
                "count_documents_in_kb",
                {"p_knowledge_base_id": knowledge_base_id}
            ).execute()
            
            if not result.data:
                return 0
            
            return result.data[0]["count"]
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

    async def get_chunk_count(self, knowledge_base_id: str) -> int:
        """Get the number of chunks in a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base.
            
        Returns:
            Number of chunks.
        """
        try:
            client = await get_db_client()
            
            result = await client.rpc(
                "count_chunks_in_kb",
                {"p_knowledge_base_id": knowledge_base_id}
            ).execute()
            
            if not result.data:
                return 0
            
            return result.data[0]["count"]
        except Exception as e:
            logger.error(f"Error getting chunk count: {str(e)}")
            return 0