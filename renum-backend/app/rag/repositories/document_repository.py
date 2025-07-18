"""
Document repository for the RAG module.

This module provides functionality for managing documents and chunks.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from app.core.logger import logger
from app.core.database import get_db_client


class DocumentRepository:
    """Repository for documents and chunks."""

    async def create(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document.
        
        Args:
            document_data: Data for the document.
            
        Returns:
            Created document.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("documents").insert(document_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create document")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise

    async def get_by_id(self, document_id: str) -> Dict[str, Any]:
        """Get a document by ID.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            Document.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("documents").select("*").eq("id", document_id).execute()
            
            if not result.data:
                raise ValueError(f"Document not found: {document_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise

    async def get_by_collection_id(self, collection_id: str) -> List[Dict[str, Any]]:
        """Get documents by collection ID.
        
        Args:
            collection_id: ID of the collection.
            
        Returns:
            List of documents.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("documents").select("*").eq("collection_id", collection_id).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting documents by collection ID: {str(e)}")
            raise

    async def update_status(self, document_id: str, status: str) -> Dict[str, Any]:
        """Update the status of a document.
        
        Args:
            document_id: ID of the document.
            status: New status.
            
        Returns:
            Updated document.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("documents").update({
                "status": status,
                "updated_at": datetime.utcnow()
            }).eq("id", document_id).execute()
            
            if not result.data:
                raise ValueError(f"Failed to update document status: {document_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise

    async def update(self, document_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a document.
        
        Args:
            document_id: ID of the document.
            document_data: New data for the document.
            
        Returns:
            Updated document.
        """
        try:
            client = await get_db_client()
            
            # Add updated_at timestamp
            document_data["updated_at"] = datetime.utcnow()
            
            result = await client.table("documents").update(document_data).eq("id", document_id).execute()
            
            if not result.data:
                raise ValueError(f"Failed to update document: {document_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    async def delete(self, document_id: str) -> bool:
        """Delete a document.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            True if the document was deleted, False otherwise.
        """
        try:
            client = await get_db_client()
            
            # Delete document chunks first
            await client.table("document_chunks").delete().eq("document_id", document_id).execute()
            
            # Delete document versions
            await client.table("document_versions").delete().eq("document_id", document_id).execute()
            
            # Delete document usage stats
            await client.table("document_usage_stats").delete().eq("document_id", document_id).execute()
            
            # Delete processing jobs
            await client.table("processing_jobs").delete().eq("document_id", document_id).execute()
            
            # Delete document
            result = await client.table("documents").delete().eq("id", document_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def create_chunk(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        chunk_index: int,
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> Dict[str, Any]:
        """Create a document chunk.
        
        Args:
            chunk_id: ID of the chunk.
            document_id: ID of the document.
            content: Content of the chunk.
            chunk_index: Index of the chunk.
            metadata: Metadata for the chunk.
            embedding: Embedding for the chunk.
            
        Returns:
            Created chunk.
        """
        try:
            client = await get_db_client()
            
            # Create chunk
            chunk_data = {
                "id": chunk_id,
                "document_id": document_id,
                "content": content,
                "chunk_index": chunk_index,
                "metadata": metadata,
                "created_at": datetime.utcnow()
            }
            
            result = await client.table("document_chunks").insert(chunk_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create document chunk")
            
            # Store embedding
            await client.rpc(
                "update_chunk_embedding",
                {
                    "p_chunk_id": chunk_id,
                    "p_embedding": embedding
                }
            ).execute()
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating document chunk: {str(e)}")
            raise

    async def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get chunks by document ID.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            List of chunks.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("document_chunks").select("*").eq("document_id", document_id).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting chunks by document ID: {str(e)}")
            raise

    async def create_version(
        self,
        document_id: str,
        version_number: int,
        change_type: str,
        changed_by: Optional[str] = None,
        change_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a document version.
        
        Args:
            document_id: ID of the document.
            version_number: Version number.
            change_type: Type of change.
            changed_by: ID of the user who made the change.
            change_description: Description of the change.
            
        Returns:
            Created version.
        """
        try:
            client = await get_db_client()
            
            version_data = {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "version_number": version_number,
                "change_type": change_type,
                "changed_by": changed_by,
                "change_description": change_description,
                "created_at": datetime.utcnow()
            }
            
            result = await client.table("document_versions").insert(version_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create document version")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating document version: {str(e)}")
            raise

    async def get_versions_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get versions by document ID.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            List of versions.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("document_versions").select("*").eq("document_id", document_id).order("version_number.desc").execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting versions by document ID: {str(e)}")
            raise