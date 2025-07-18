"""
API endpoints for document management in the RAG module.

This module provides FastAPI endpoints for managing documents.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File, Form, Body
from pydantic import UUID4, HttpUrl, BaseModel, Field

from app.core.auth import get_current_user_id
from app.core.logger import logger
from app.core.config import is_feature_enabled

from app.rag.models.api import (
    DocumentResponse, ProcessingJobResponse
)
from app.rag.repositories.document_repository import DocumentRepository
from app.rag.repositories.collection_repository import CollectionRepository
from app.rag.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.rag.repositories.processing_job_repository import ProcessingJobRepository
from app.rag.services.ingestion_service import IngestionCoordinator


# Create router
router = APIRouter(tags=["rag"])


class TextDocumentRequest(BaseModel):
    """Request model for adding a text document."""
    collection_id: UUID4
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    chunking_strategy: str = Field(default="fixed_size")


class UrlDocumentRequest(BaseModel):
    """Request model for adding a URL document."""
    collection_id: UUID4
    url: HttpUrl
    name: Optional[str] = None
    description: Optional[str] = None
    use_firecrawl: bool = True
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    chunking_strategy: str = Field(default="fixed_size")


@router.get("/collections/{collection_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    collection_id: UUID4 = Path(..., description="The ID of the collection"),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all documents in a collection.
    
    This endpoint retrieves all documents in a specific collection.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the collection exists
        collection_repository = CollectionRepository()
        try:
            collection = await collection_repository.get_by_id(str(collection_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {collection_id}"
            )
        
        # Check if the collection belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this collection"
            )
        
        # Initialize repository
        document_repository = DocumentRepository()
        
        # Get documents
        documents = await document_repository.get_by_collection_id(str(collection_id))
        
        # Convert to response models
        responses = [
            DocumentResponse.from_entity(document) for document in documents
        ]
        
        return responses
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.post("/documents/file", response_model=ProcessingJobResponse, status_code=201)
async def upload_file(
    collection_id: str = Form(...),
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    chunking_strategy: str = Form("fixed_size"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a file document.
    
    This endpoint uploads a file and processes it as a document.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the collection exists
        collection_repository = CollectionRepository()
        try:
            collection = await collection_repository.get_by_id(collection_id)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {collection_id}"
            )
        
        # Check if the collection belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to upload to this collection"
            )
        
        # Read file content
        content = await file.read()
        
        # Get file size
        file_size = len(content)
        
        # Get file type
        file_type = file.content_type
        
        # Get file name
        file_name = name or file.filename
        
        # Initialize ingestion coordinator
        coordinator = IngestionCoordinator()
        
        # Process document
        job_id = await coordinator.process_document(
            source_type="file",
            collection_id=collection_id,
            content=content,
            metadata={
                "name": file_name,
                "description": description,
                "file_type": file_type,
                "file_size": file_size,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "chunking_strategy": chunking_strategy
            }
        )
        
        # Get processing job
        processing_job_repository = ProcessingJobRepository()
        job = await processing_job_repository.get_by_id(job_id)
        
        # Convert to response model
        response = ProcessingJobResponse(
            id=job["id"],
            document_id=job["document_id"],
            status=job["status"],
            progress=job["progress"],
            error_message=job.get("error_message"),
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.post("/documents/url", response_model=ProcessingJobResponse, status_code=201)
async def add_url(
    request: UrlDocumentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a URL document.
    
    This endpoint adds a URL and processes it as a document.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the collection exists
        collection_repository = CollectionRepository()
        try:
            collection = await collection_repository.get_by_id(str(request.collection_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {request.collection_id}"
            )
        
        # Check if the collection belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to add to this collection"
            )
        
        # Initialize ingestion coordinator
        coordinator = IngestionCoordinator()
        
        # Process document
        job_id = await coordinator.process_document(
            source_type="url",
            collection_id=str(request.collection_id),
            content=str(request.url),
            metadata={
                "name": request.name or str(request.url),
                "description": request.description,
                "url": str(request.url),
                "use_firecrawl": request.use_firecrawl,
                "chunk_size": request.chunk_size,
                "chunk_overlap": request.chunk_overlap,
                "chunking_strategy": request.chunking_strategy
            }
        )
        
        # Get processing job
        processing_job_repository = ProcessingJobRepository()
        job = await processing_job_repository.get_by_id(job_id)
        
        # Convert to response model
        response = ProcessingJobResponse(
            id=job["id"],
            document_id=job["document_id"],
            status=job["status"],
            progress=job["progress"],
            error_message=job.get("error_message"),
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error adding URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add URL: {str(e)}")


@router.post("/documents/text", response_model=ProcessingJobResponse, status_code=201)
async def add_text(
    request: TextDocumentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a text document.
    
    This endpoint adds text and processes it as a document.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the collection exists
        collection_repository = CollectionRepository()
        try:
            collection = await collection_repository.get_by_id(str(request.collection_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {request.collection_id}"
            )
        
        # Check if the collection belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to add to this collection"
            )
        
        # Initialize ingestion coordinator
        coordinator = IngestionCoordinator()
        
        # Process document
        job_id = await coordinator.process_document(
            source_type="text",
            collection_id=str(request.collection_id),
            content=request.content,
            metadata={
                "name": request.name,
                "description": request.description,
                "chunk_size": request.chunk_size,
                "chunk_overlap": request.chunk_overlap,
                "chunking_strategy": request.chunking_strategy
            }
        )
        
        # Get processing job
        processing_job_repository = ProcessingJobRepository()
        job = await processing_job_repository.get_by_id(job_id)
        
        # Convert to response model
        response = ProcessingJobResponse(
            id=job["id"],
            document_id=job["document_id"],
            status=job["status"],
            progress=job["progress"],
            error_message=job.get("error_message"),
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error adding text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add text: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID4 = Path(..., description="The ID of the document"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get details of a specific document.
    
    This endpoint retrieves details of a document by its ID.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        document_repository = DocumentRepository()
        
        # Get document
        try:
            document = await document_repository.get_by_id(str(document_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if the document belongs to the user's client
        collection_repository = CollectionRepository()
        collection = await collection_repository.get_by_id(document["collection_id"])
        
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this document"
            )
        
        # Get chunk count
        chunks = await document_repository.get_chunks_by_document_id(str(document_id))
        document["chunk_count"] = len(chunks)
        
        # Get version count
        versions = await document_repository.get_versions_by_document_id(str(document_id))
        document["version_count"] = len(versions)
        
        # Convert to response model
        response = DocumentResponse.from_entity(document)
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID4 = Path(..., description="The ID of the document"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a document.
    
    This endpoint deletes a document and all its associated chunks.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        document_repository = DocumentRepository()
        
        # Get document
        try:
            document = await document_repository.get_by_id(str(document_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if the document belongs to the user's client
        collection_repository = CollectionRepository()
        collection = await collection_repository.get_by_id(document["collection_id"])
        
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this document"
            )
        
        # Delete document
        success = await document_repository.delete(str(document_id))
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {document_id}"
            )
        
        # Return no content
        return None
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/documents/{document_id}/chunks", response_model=List[Dict[str, Any]])
async def list_chunks(
    document_id: UUID4 = Path(..., description="The ID of the document"),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all chunks in a document.
    
    This endpoint retrieves all chunks in a specific document.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        document_repository = DocumentRepository()
        
        # Get document
        try:
            document = await document_repository.get_by_id(str(document_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
        
        # Check if the document belongs to the user's client
        collection_repository = CollectionRepository()
        collection = await collection_repository.get_by_id(document["collection_id"])
        
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this document"
            )
        
        # Get chunks
        chunks = await document_repository.get_chunks_by_document_id(str(document_id))
        
        # Remove embeddings from response
        for chunk in chunks:
            if "embedding" in chunk:
                del chunk["embedding"]
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error listing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list chunks: {str(e)}")


@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_job_status(
    job_id: UUID4 = Path(..., description="The ID of the processing job"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get the status of a processing job.
    
    This endpoint retrieves the status of a processing job by its ID.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        processing_job_repository = ProcessingJobRepository()
        
        # Get processing job
        try:
            job = await processing_job_repository.get_by_id(str(job_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Processing job not found: {job_id}"
            )
        
        # Check if the job belongs to the user's client
        document_repository = DocumentRepository()
        document = await document_repository.get_by_id(job["document_id"])
        
        collection_repository = CollectionRepository()
        collection = await collection_repository.get_by_id(document["collection_id"])
        
        kb_repository = KnowledgeBaseRepository()
        kb = await kb_repository.get_by_id(collection["knowledge_base_id"])
        
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this job"
            )
        
        # Convert to response model
        response = ProcessingJobResponse(
            id=job["id"],
            document_id=job["document_id"],
            status=job["status"],
            progress=job["progress"],
            error_message=job.get("error_message"),
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")