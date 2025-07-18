"""
Example of using the agent RAG integration.

This module demonstrates how to use the agent RAG integration endpoint.
"""

import asyncio
import json
import httpx
from typing import Dict, Any


async def enrich_prompt_with_rag(
    api_url: str,
    token: str,
    query: str,
    client_id: str,
    agent_id: str,
    original_prompt: str
) -> Dict[str, Any]:
    """
    Enrich a prompt with context from the RAG module.
    
    Args:
        api_url: Base URL of the API.
        token: Authentication token.
        query: User query to retrieve relevant information for.
        client_id: ID of the client.
        agent_id: ID of the agent.
        original_prompt: Original prompt to enrich.
        
    Returns:
        Response from the API containing the enriched prompt.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "client_id": client_id,
        "agent_id": agent_id,
        "original_prompt": original_prompt,
        "max_tokens": 4000,
        "top_k": 5
    }
    
    endpoint = f"{api_url}/api/knowledge-base/agent-rag/query"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        
        return response.json()


async def submit_retrieval_feedback(
    api_url: str,
    token: str,
    message_id: str,
    chunk_id: str,
    relevance_score: int,
    feedback_text: str = None
) -> Dict[str, Any]:
    """
    Submit feedback on the relevance of a retrieved chunk.
    
    Args:
        api_url: Base URL of the API.
        token: Authentication token.
        message_id: ID of the message.
        chunk_id: ID of the chunk.
        relevance_score: Relevance score (1-5).
        feedback_text: Optional feedback text.
        
    Returns:
        Response from the API.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message_id": message_id,
        "chunk_id": chunk_id,
        "relevance_score": relevance_score,
        "feedback_text": feedback_text
    }
    
    endpoint = f"{api_url}/api/knowledge-base/agent-rag/feedback"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        
        return response.json()


async def main():
    """Example usage of the agent RAG integration."""
    # Configuration
    api_url = "http://localhost:8000"
    token = "your_auth_token"
    client_id = "client-123"
    agent_id = "agent-456"
    
    # Example query
    query = "What are the key features of our product?"
    original_prompt = "You are a helpful assistant. Please answer the user's question."
    
    try:
        # Enrich prompt with RAG context
        result = await enrich_prompt_with_rag(
            api_url=api_url,
            token=token,
            query=query,
            client_id=client_id,
            agent_id=agent_id,
            original_prompt=original_prompt
        )
        
        print("Enriched Prompt:")
        print(result["enriched_prompt"])
        print("\nSources Used:")
        for source in result["used_sources"]:
            print(f"- {source['document_name']} (Similarity: {source['similarity']:.2f})")
        
        print("\nMetadata:")
        print(json.dumps(result["metadata"], indent=2))
        
        # Example of submitting feedback
        if result["used_sources"]:
            source = result["used_sources"][0]
            await submit_retrieval_feedback(
                api_url=api_url,
                token=token,
                message_id="message-789",
                chunk_id=source["chunk_id"],
                relevance_score=5,  # Very relevant
                feedback_text="This information was exactly what I needed."
            )
            print("\nFeedback submitted successfully.")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())