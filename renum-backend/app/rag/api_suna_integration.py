"""
API endpoints for Suna Core integration in the RAG module.

This module provides FastAPI endpoints for integrating with Suna Core.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_id
from app.core.logger import logger
from app.core.config import is_feature_enabled
from app.core.database import get_db_client

from app.rag.services.suna_integration_service import SunaIntegrationService


# Create router
router = APIRouter(tags=["rag"])


class SunaEnrichRequest(BaseModel):
    """Request model for Suna prompt enrichment."""
    query: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    agent_id: Optional[str] = None
    original_prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=4000, ge=100, le=8000)
    top_k: int = Field(default=5, ge=1, le=20)


class SunaEnrichResponse(BaseModel):
    """Response model for Suna prompt enrichment."""
    enriched_prompt: str
    used_sources: list
    metadata: Dict[str, Any]


class SunaExecuteRequest(BaseModel):
    """Request model for Suna execution with RAG."""
    query: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    original_prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=4000, ge=100, le=8000)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/suna/enrich", response_model=SunaEnrichResponse)
async def enrich_prompt_for_suna(
    request: SunaEnrichRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Enrich a prompt with relevant knowledge for Suna Core.
    
    This endpoint:
    1. Receives a query and prompt from the client
    2. Retrieves relevant chunks from the knowledge bases
    3. Enriches the prompt with the retrieved context
    4. Returns the enriched prompt to the client
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize service
        suna_integration_service = SunaIntegrationService()
        
        # Enrich prompt
        result = await suna_integration_service.enrich_prompt_for_suna(
            query=request.query,
            client_id=request.client_id,
            agent_id=request.agent_id,
            original_prompt=request.original_prompt,
            max_tokens=request.max_tokens,
            top_k=request.top_k
        )
        
        # Return enriched prompt
        return SunaEnrichResponse(
            enriched_prompt=result["enriched_prompt"],
            used_sources=result["used_sources"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Error enriching prompt for Suna: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enrich prompt: {str(e)}")


@router.post("/suna/execute")
async def execute_suna_with_rag(
    request: SunaExecuteRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Execute a Suna agent with RAG-enriched prompt.
    
    This endpoint:
    1. Receives a query and prompt from the client
    2. Retrieves relevant chunks from the knowledge bases
    3. Enriches the prompt with the retrieved context
    4. Sends the enriched prompt to Suna Core
    5. Returns the response from Suna Core
    """
    if not is_feature_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize service
        suna_integration_service = SunaIntegrationService()
        
        # Send enriched prompt to Suna
        result = await suna_integration_service.send_enriched_prompt_to_suna(
            query=request.query,
            client_id=request.client_id,
            agent_id=request.agent_id,
            original_prompt=request.original_prompt,
            max_tokens=request.max_tokens,
            top_k=request.top_k
        )
        
        # Return Suna response
        return result
        
    except Exception as e:
        logger.error(f"Error executing Suna with RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute Suna with RAG: {str(e)}")