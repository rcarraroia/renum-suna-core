"""
Processing job repository for the RAG module.

This module provides functionality for managing processing jobs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logger import logger
from app.core.database import get_db_client


class ProcessingJobRepository:
    """Repository for processing jobs."""

    async def create(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a processing job.
        
        Args:
            job_data: Data for the processing job.
            
        Returns:
            Created processing job.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("processing_jobs").insert(job_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create processing job")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating processing job: {str(e)}")
            raise

    async def get_by_id(self, job_id: str) -> Dict[str, Any]:
        """Get a processing job by ID.
        
        Args:
            job_id: ID of the processing job.
            
        Returns:
            Processing job.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("processing_jobs").select("*").eq("id", job_id).execute()
            
            if not result.data:
                raise ValueError(f"Processing job not found: {job_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error getting processing job: {str(e)}")
            raise

    async def get_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get processing jobs by document ID.
        
        Args:
            document_id: ID of the document.
            
        Returns:
            List of processing jobs.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("processing_jobs").select("*").eq("document_id", document_id).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting processing jobs by document ID: {str(e)}")
            raise

    async def update_status(
        self,
        job_id: str,
        status: str,
        progress: float,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of a processing job.
        
        Args:
            job_id: ID of the processing job.
            status: New status.
            progress: New progress.
            error_message: Error message if any.
            
        Returns:
            Updated processing job.
        """
        try:
            client = await get_db_client()
            
            update_data = {
                "status": status,
                "progress": progress,
                "updated_at": datetime.utcnow()
            }
            
            if error_message is not None:
                update_data["error_message"] = error_message
            
            result = await client.table("processing_jobs").update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                raise ValueError(f"Failed to update processing job status: {job_id}")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating processing job status: {str(e)}")
            raise

    async def delete(self, job_id: str) -> bool:
        """Delete a processing job.
        
        Args:
            job_id: ID of the processing job.
            
        Returns:
            True if the processing job was deleted, False otherwise.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("processing_jobs").delete().eq("id", job_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting processing job: {str(e)}")
            raise

    async def get_by_status(self, status: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get processing jobs by status.
        
        Args:
            status: Status to filter by.
            limit: Maximum number of jobs to return.
            
        Returns:
            List of processing jobs.
        """
        try:
            client = await get_db_client()
            
            result = await client.table("processing_jobs").select("*").eq("status", status).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting processing jobs by status: {str(e)}")
            raise