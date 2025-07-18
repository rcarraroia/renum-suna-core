"""
Suna Core integration service for the RAG module.

This module provides functionality for integrating with Suna Core for prompt enrichment.
"""

import httpx
from typing import Dict, Any, List, Optional
import json

from app.core.logger import logger
from app.core.config import get_settings
from app.core.database import get_db_client
from app.rag.services.retrieval_service import RetrievalService


class SunaIntegrationService:
    """Service for integrating with Suna Core."""

    def __init__(
        self,
        retrieval_service: RetrievalService = None,
        suna_api_url: str = None,
        suna_api_key: str = None
    ):
        """Initialize the Suna integration service.
        
        Args:
            retrieval_service: Service for retrieving relevant chunks.
            suna_api_url: URL of the Suna Core API.
            suna_api_key: API key for the Suna Core API.
        """
        self.retrieval_service = retrieval_service or RetrievalService()
        self.suna_api_url = suna_api_url or get_settings().suna_api_url
        self.suna_api_key = suna_api_key or get_settings().suna_api_key

    async def enrich_prompt_for_suna(
        self,
        query: str,
        client_id: str,
        agent_id: Optional[str],
        original_prompt: str,
        max_tokens: int = 4000,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Enrich a prompt with relevant knowledge for Suna Core.
        
        Args:
            query: Query to retrieve relevant chunks.
            client_id: ID of the client.
            agent_id: ID of the agent.
            original_prompt: Original prompt to enrich.
            max_tokens: Maximum number of tokens in the enriched prompt.
            top_k: Number of top chunks to retrieve.
            
        Returns:
            Dictionary with enriched prompt and metadata.
        """
        try:
            # Get knowledge bases for the client
            client = await get_db_client()
            kb_result = await client.rpc(
                'get_client_knowledge_bases',
                {'p_client_id': client_id}
            ).execute()
            
            if not kb_result.data:
                # No knowledge bases found, return original prompt
                return {
                    "enriched_prompt": original_prompt,
                    "used_sources": [],
                    "metadata": {"knowledge_bases_found": 0, "collections_found": 0, "chunks_retrieved": 0}
                }
            
            # Get collections for these knowledge bases
            knowledge_base_ids = [kb['id'] for kb in kb_result.data]
            collection_result = await client.rpc(
                'get_collections_for_knowledge_bases',
                {'p_knowledge_base_ids': knowledge_base_ids}
            ).execute()
            
            if not collection_result.data:
                # No collections found, return original prompt
                return {
                    "enriched_prompt": original_prompt,
                    "used_sources": [],
                    "metadata": {"knowledge_bases_found": len(knowledge_base_ids), "collections_found": 0, "chunks_retrieved": 0}
                }
            
            # Get collection IDs
            collection_ids = [col['id'] for col in collection_result.data]
            
            # Retrieve relevant chunks
            chunks = await self.retrieval_service.retrieve_relevant_chunks(
                query=query,
                collection_ids=collection_ids,
                top_k=top_k
            )
            
            if not chunks:
                # No relevant chunks found, return original prompt
                return {
                    "enriched_prompt": original_prompt,
                    "used_sources": [],
                    "metadata": {
                        "knowledge_bases_found": len(knowledge_base_ids),
                        "collections_found": len(collection_ids),
                        "chunks_retrieved": 0
                    }
                }
            
            # Enrich prompt with retrieved context
            from app.rag.services.llm_integration_service import LLMIntegrationService
            llm_integration_service = LLMIntegrationService(max_context_length=max_tokens)
            
            enriched_prompt, used_chunks = await llm_integration_service.enrich_prompt(
                original_prompt=original_prompt,
                relevant_chunks=chunks,
                max_tokens=max_tokens
            )
            
            # Track usage if agent_id is provided
            if agent_id and used_chunks:
                chunk_ids = [chunk['id'] for chunk in used_chunks]
                await self.retrieval_service.track_chunk_usage(
                    chunk_ids=chunk_ids,
                    agent_id=agent_id,
                    client_id=client_id
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
            return {
                "enriched_prompt": enriched_prompt,
                "used_sources": used_sources,
                "metadata": {
                    "knowledge_bases_found": len(knowledge_base_ids),
                    "collections_found": len(collection_ids),
                    "chunks_retrieved": len(chunks),
                    "chunks_used": len(used_chunks)
                }
            }
        except Exception as e:
            logger.error(f"Error enriching prompt for Suna: {str(e)}")
            # Return original prompt in case of error
            return {
                "enriched_prompt": original_prompt,
                "used_sources": [],
                "metadata": {"error": str(e)}
            }

    async def send_enriched_prompt_to_suna(
        self,
        query: str,
        client_id: str,
        agent_id: Optional[str],
        original_prompt: str,
        max_tokens: int = 4000,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Send an enriched prompt to Suna Core.
        
        Args:
            query: Query to retrieve relevant chunks.
            client_id: ID of the client.
            agent_id: ID of the agent.
            original_prompt: Original prompt to enrich.
            max_tokens: Maximum number of tokens in the enriched prompt.
            top_k: Number of top chunks to retrieve.
            
        Returns:
            Response from Suna Core.
        """
        try:
            # Enrich prompt
            enrichment_result = await self.enrich_prompt_for_suna(
                query=query,
                client_id=client_id,
                agent_id=agent_id,
                original_prompt=original_prompt,
                max_tokens=max_tokens,
                top_k=top_k
            )
            
            enriched_prompt = enrichment_result["enriched_prompt"]
            
            # Send to Suna Core
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.suna_api_url}/api/v1/agents/{agent_id}/execute",
                    headers={
                        "Authorization": f"Bearer {self.suna_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": enriched_prompt,
                        "client_id": client_id,
                        "metadata": {
                            "rag_enriched": True,
                            "rag_metadata": enrichment_result["metadata"],
                            "rag_sources": enrichment_result["used_sources"]
                        }
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Add RAG metadata to the response
                result["rag_metadata"] = enrichment_result["metadata"]
                result["rag_sources"] = enrichment_result["used_sources"]
                
                return result
        except Exception as e:
            logger.error(f"Error sending enriched prompt to Suna: {str(e)}")
            raise