"""
Agent RAG integration for the Renum platform.

This module provides endpoints for agents to access knowledge stored in the RAG module.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field, UUID4

from utils.auth_utils import get_current_user_id_from_jwt
from services.supabase import DBConnection
from utils.logger import logger
from flags.flags import is_enabled

from knowledge_base.rag.services.retrieval_service import RetrievalService
from knowledge_base.rag.services.llm_integration_service import LLMIntegrationService


router = APIRouter(prefix="/agent-rag", tags=["agent-rag"])

db = DBConnection()


class AgentQueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    agent_id: Optional[str] = None
    original_prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=4000, ge=100, le=8000)
    top_k: int = Field(default=5, ge=1, le=20)


class AgentQueryResponse(BaseModel):
    """Response model for agent queries."""
    enriched_prompt: str
    used_sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    request: AgentQueryRequest,
    user_id: str = Depends(get_current_user_id_from_jwt)
):
    """
    Process an agent query and enrich the prompt with relevant knowledge.
    
    This endpoint:
    1. Receives a query from an agent
    2. Identifies relevant knowledge bases for the client
    3. Retrieves relevant chunks from the knowledge bases
    4. Enriches the prompt with the retrieved context
    5. Returns the enriched prompt to the agent
    """
    if not await is_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        # Initialize services
        retrieval_service = RetrievalService()
        llm_integration_service = LLMIntegrationService(max_context_length=request.max_tokens)
        
        # Get knowledge bases for the client
        client = await db.client
        kb_result = await client.rpc(
            'get_client_knowledge_bases',
            {'p_client_id': request.client_id}
        ).execute()
        
        if not kb_result.data:
            # No knowledge bases found, return original prompt
            return AgentQueryResponse(
                enriched_prompt=request.original_prompt,
                used_sources=[],
                metadata={"knowledge_bases_found": 0, "collections_found": 0, "chunks_retrieved": 0}
            )
        
        # Get collections for these knowledge bases
        knowledge_base_ids = [kb['id'] for kb in kb_result.data]
        collection_result = await client.rpc(
            'get_collections_for_knowledge_bases',
            {'p_knowledge_base_ids': knowledge_base_ids}
        ).execute()
        
        if not collection_result.data:
            # No collections found, return original prompt
            return AgentQueryResponse(
                enriched_prompt=request.original_prompt,
                used_sources=[],
                metadata={"knowledge_bases_found": len(knowledge_base_ids), "collections_found": 0, "chunks_retrieved": 0}
            )
        
        # Get collection IDs
        collection_ids = [col['id'] for col in collection_result.data]
        
        # Retrieve relevant chunks
        chunks = await retrieval_service.retrieve_relevant_chunks(
            query=request.query,
            collection_ids=collection_ids,
            top_k=request.top_k
        )
        
        if not chunks:
            # No relevant chunks found, return original prompt
            return AgentQueryResponse(
                enriched_prompt=request.original_prompt,
                used_sources=[],
                metadata={
                    "knowledge_bases_found": len(knowledge_base_ids),
                    "collections_found": len(collection_ids),
                    "chunks_retrieved": 0
                }
            )
        
        # Enrich prompt with retrieved context
        enriched_prompt, used_chunks = await llm_integration_service.enrich_prompt(
            original_prompt=request.original_prompt,
            relevant_chunks=chunks,
            max_tokens=request.max_tokens
        )
        
        # Track usage if agent_id is provided
        if request.agent_id and used_chunks:
            chunk_ids = [chunk['id'] for chunk in used_chunks]
            await retrieval_service.track_chunk_usage(
                chunk_ids=chunk_ids,
                agent_id=request.agent_id,
                client_id=request.client_id
            )
        
        # Format sources for response
        used_sources = []
        for chunk in used_chunks:
            source = {
                "chunk_id": chunk['id'],
                "document_id": chunk['document_id'],
                "document_name": chunk['document']['name'],
                "collection_id": chunk['document']['collection_id'],
                "collection_name": chunk['document']['collection_name'],
                "similarity": chunk.get('similarity', 0),
                "content_preview": chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
            }
            used_sources.append(source)
        
        # Return enriched prompt
        return AgentQueryResponse(
            enriched_prompt=enriched_prompt,
            used_sources=used_sources,
            metadata={
                "knowledge_bases_found": len(knowledge_base_ids),
                "collections_found": len(collection_ids),
                "chunks_retrieved": len(chunks),
                "chunks_used": len(used_chunks)
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing agent RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.post("/feedback")
async def submit_retrieval_feedback(
    message_id: str = Body(...),
    chunk_id: str = Body(...),
    relevance_score: int = Body(..., ge=1, le=5),
    feedback_text: Optional[str] = Body(None),
    user_id: str = Depends(get_current_user_id_from_jwt)
):
    """
    Submit feedback on the relevance of a retrieved chunk.
    
    This endpoint allows agents or users to provide feedback on the relevance
    of chunks retrieved by the RAG system, which can be used to improve
    retrieval quality over time.
    """
    if not await is_enabled("rag_module"):
        raise HTTPException(
            status_code=403, 
            detail="The RAG module is not available at the moment."
        )
    
    try:
        client = await db.client
        
        # Insert feedback
        result = await client.table('retrieval_feedback').insert({
            'message_id': message_id,
            'chunk_id': chunk_id,
            'relevance_score': relevance_score,
            'user_id': user_id,
            'feedback_text': feedback_text
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
        
        return {"success": True, "message": "Feedback submitted successfully"}
        
    except Exception as e:
        logger.error(f"Error submitting retrieval feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")