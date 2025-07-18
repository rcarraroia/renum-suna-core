"""
API endpoints for knowledge base management in the RAG module.

This module provides FastAPI endpoints for managing knowledge bases.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import UUID4

from app.core.auth import get_current_user_id
from app.core.logger import logger
from app.core.config import is_feature_enabled

from app.rag.models.api import (
    KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate
)
from app.rag.repositories.knowledge_base_repository import KnowledgeBaseRepository


# Create router
router = APIRouter(prefix="/rag/bases", tags=["rag"])


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    user_id: str = Depends(get_current_user_id)
):
    """
    List all knowledge bases for the current user's client.
    
    This endpoint retrieves all knowledge bases associated with the client
    of the authenticated user.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Get client ID for the current user
        # In a real implementation, you would get the client ID from the user's profile
        # For now, we'll use the user ID as the client ID
        client_id = user_id
        
        # Initialize repository
        repository = KnowledgeBaseRepository()
        
        # Get knowledge bases
        knowledge_bases = await repository.get_by_client_id(client_id)
        
        # Convert to response models
        responses = [
            KnowledgeBaseResponse.from_entity(kb) for kb in knowledge_bases
        ]
        
        return responses
        
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list knowledge bases: {str(e)}")


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new knowledge base.
    
    This endpoint creates a new knowledge base for the specified client.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = KnowledgeBaseRepository()
        
        # Create knowledge base
        created_kb = await repository.create(
            name=knowledge_base.name,
            client_id=knowledge_base.client_id,
            description=knowledge_base.description
        )
        
        # Convert to response model
        response = KnowledgeBaseResponse.from_entity(created_kb)
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create knowledge base: {str(e)}")


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: UUID4 = Path(..., description="The ID of the knowledge base"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get details of a specific knowledge base.
    
    This endpoint retrieves details of a knowledge base by its ID.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = KnowledgeBaseRepository()
        
        # Get knowledge base
        knowledge_base = await repository.get_by_id(str(knowledge_base_id))
        
        # Check if the knowledge base belongs to the user's client
        # In a real implementation, you would check if the knowledge base's client ID
        # matches the client ID of the authenticated user
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if knowledge_base["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this knowledge base"
            )
        
        # Convert to response model
        response = KnowledgeBaseResponse.from_entity(knowledge_base)
        
        return response
        
    except ValueError as e:
        logger.error(f"Knowledge base not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {knowledge_base_id}")
    except Exception as e:
        logger.error(f"Error getting knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base: {str(e)}")


@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_update: KnowledgeBaseUpdate,
    knowledge_base_id: UUID4 = Path(..., description="The ID of the knowledge base"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a knowledge base.
    
    This endpoint updates a knowledge base with the provided data.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = KnowledgeBaseRepository()
        
        # Check if the knowledge base exists and belongs to the user's client
        existing_kb = await repository.get_by_id(str(knowledge_base_id))
        
        # Check if the knowledge base belongs to the user's client
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if existing_kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this knowledge base"
            )
        
        # Update knowledge base
        updated_kb = await repository.update(
            knowledge_base_id=str(knowledge_base_id),
            name=knowledge_base_update.name,
            description=knowledge_base_update.description
        )
        
        # Convert to response model
        response = KnowledgeBaseResponse.from_entity(updated_kb)
        
        return response
        
    except ValueError as e:
        logger.error(f"Knowledge base not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {knowledge_base_id}")
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge base: {str(e)}")


@router.delete("/{knowledge_base_id}", status_code=204)
async def delete_knowledge_base(
    knowledge_base_id: UUID4 = Path(..., description="The ID of the knowledge base"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a knowledge base.
    
    This endpoint deletes a knowledge base and all its associated collections,
    documents, and chunks.
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize repository
        repository = KnowledgeBaseRepository()
        
        # Check if the knowledge base exists and belongs to the user's client
        existing_kb = await repository.get_by_id(str(knowledge_base_id))
        
        # Check if the knowledge base belongs to the user's client
        client_id = user_id  # For now, we'll use the user ID as the client ID
        if existing_kb["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this knowledge base"
            )
        
        # Delete knowledge base
        success = await repository.delete(str(knowledge_base_id))
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete knowledge base: {knowledge_base_id}"
            )
        
        # Return no content
        return None
        
    except ValueError as e:
        logger.error(f"Knowledge base not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {knowledge_base_id}")
    except Exception as e:
        logger.error(f"Error deleting knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge base: {str(e)}")