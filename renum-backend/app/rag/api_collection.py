"""
API endpoints for collection management in the RAG module.

This module provides FastAPI endpoints for managing collections.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import UUID4

from app.core.auth import get_current_user_id
from app.core.logger import logger
from app.core.config import is_feature_enabled

from app.rag.models.api import (
    CollectionCreate, CollectionResponse, CollectionUpdate
)
from app.rag.repositories.collection_repository import CollectionRepository
from app.rag.repositories.knowledge_base_repository import KnowledgeBaseRepository


# Create router
router = APIRouter(tags=["rag"])


@router.get("/bases/{knowledge_base_id}/collections", response_model=List[CollectionResponse])
async def list_collections(
    knowledge_base_id: UUID4 = Path(..., description="The ID of the knowledge base"),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all collections in a knowledge base.
    
    This endpoint retrieves all collections in a specific knowledge base.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the knowledge base exists and belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        try:
            kb = await kb_repository.get_by_id(str(knowledge_base_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge base not found: {knowledge_base_id}"
            )
        
        # Check if the knowledge base belongs to the user's client
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this knowledge base"
            )
        
        # Initialize repository
        repository = CollectionRepository()
        
        # Get collections
        collections = await repository.get_by_knowledge_base_id(str(knowledge_base_id))
        
        # Add document count to each collection
        for collection in collections:
            document_count = await repository.get_document_count(collection["id"])
            collection["document_count"] = document_count
        
        # Convert to response models
        responses = [
            CollectionResponse.from_entity(collection) for collection in collections
        ]
        
        return responses
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(
    collection: CollectionCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new collection.
    
    This endpoint creates a new collection in a knowledge base.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Check if the knowledge base exists and belongs to the user's client
        kb_repository = KnowledgeBaseRepository()
        try:
            kb = await kb_repository.get_by_id(str(collection.knowledge_base_id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge base not found: {collection.knowledge_base_id}"
            )
        
        # Check if the knowledge base belongs to the user's client
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to create a collection in this knowledge base"
            )
        
        # Initialize repository
        repository = CollectionRepository()
        
        # Create collection
        created_collection = await repository.create(
            knowledge_base_id=str(collection.knowledge_base_id),
            name=collection.name,
            description=collection.description
        )
        
        # Convert to response model
        response = CollectionResponse.from_entity(created_collection)
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID4 = Path(..., description="The ID of the collection"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get details of a specific collection.
    
    This endpoint retrieves details of a collection by its ID.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = CollectionRepository()
        
        # Get collection
        try:
            collection = await repository.get_by_id(str(collection_id))
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
        
        # Add document count
        document_count = await repository.get_document_count(str(collection_id))
        collection["document_count"] = document_count
        
        # Convert to response model
        response = CollectionResponse.from_entity(collection)
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get collection: {str(e)}")


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_update: CollectionUpdate,
    collection_id: UUID4 = Path(..., description="The ID of the collection"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a collection.
    
    This endpoint updates a collection with the provided data.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = CollectionRepository()
        
        # Check if the collection exists
        try:
            collection = await repository.get_by_id(str(collection_id))
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
                detail="You don't have permission to update this collection"
            )
        
        # Update collection
        updated_collection = await repository.update(
            collection_id=str(collection_id),
            name=collection_update.name,
            description=collection_update.description
        )
        
        # Add document count
        document_count = await repository.get_document_count(str(collection_id))
        updated_collection["document_count"] = document_count
        
        # Convert to response model
        response = CollectionResponse.from_entity(updated_collection)
        
        return response
        
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update collection: {str(e)}")


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: UUID4 = Path(..., description="The ID of the collection"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a collection.
    
    This endpoint deletes a collection and all its associated documents and chunks.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = CollectionRepository()
        
        # Check if the collection exists
        try:
            collection = await repository.get_by_id(str(collection_id))
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
                detail="You don't have permission to delete this collection"
            )
        
        # Delete collection
        success = await repository.delete(str(collection_id))
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete collection: {collection_id}"
            )
        
        # Return no content
        return None
        
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")