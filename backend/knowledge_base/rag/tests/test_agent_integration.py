"""
Tests for the agent RAG integration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from datetime import datetime

from api import app
from knowledge_base.agent_rag_integration import (
    agent_query,
    AgentQueryRequest,
    AgentQueryResponse
)


@pytest.fixture
def mock_retrieval_service():
    mock = AsyncMock()
    mock.retrieve_relevant_chunks = AsyncMock()
    mock.track_chunk_usage = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_llm_integration_service():
    mock = AsyncMock()
    mock.enrich_prompt = AsyncMock()
    return mock


@pytest.fixture
def mock_db_client():
    mock = AsyncMock()
    mock.rpc().execute = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_agent_query_with_results(
    mock_retrieval_service,
    mock_llm_integration_service,
    mock_db_client
):
    """Test agent query with results."""
    # Mock database responses
    client_id = str(uuid.uuid4())
    kb_id = str(uuid.uuid4())
    collection_id = str(uuid.uuid4())
    
    mock_db_client.rpc().execute.side_effect = [
        # Knowledge bases response
        MagicMock(data=[{'id': kb_id, 'name': 'Test KB'}]),
        # Collections response
        MagicMock(data=[{'id': collection_id, 'name': 'Test Collection'}])
    ]
    
    # Mock retrieval service
    chunk_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    chunks = [
        {
            'id': chunk_id,
            'document_id': document_id,
            'content': 'Test content',
            'chunk_index': 0,
            'metadata': {'test': 'metadata'},
            'similarity': 0.9,
            'created_at': datetime.now().isoformat(),
            'document': {
                'id': document_id,
                'name': 'Test Document',
                'source_type': 'file',
                'collection_id': collection_id,
                'collection_name': 'Test Collection'
            }
        }
    ]
    mock_retrieval_service.retrieve_relevant_chunks.return_value = chunks
    
    # Mock LLM integration service
    enriched_prompt = "Enriched prompt with context"
    mock_llm_integration_service.enrich_prompt.return_value = (enriched_prompt, chunks)
    
    # Create request
    request = AgentQueryRequest(
        query="Test query",
        client_id=client_id,
        agent_id="agent-123",
        original_prompt="Original prompt",
        max_tokens=4000,
        top_k=5
    )
    
    # Call function with mocks
    with patch('knowledge_base.agent_rag_integration.RetrievalService', return_value=mock_retrieval_service), \
         patch('knowledge_base.agent_rag_integration.LLMIntegrationService', return_value=mock_llm_integration_service), \
         patch('knowledge_base.agent_rag_integration.db.client', mock_db_client):
        
        response = await agent_query(request, user_id="user-123")
    
    # Verify response
    assert isinstance(response, AgentQueryResponse)
    assert response.enriched_prompt == enriched_prompt
    assert len(response.used_sources) == 1
    assert response.used_sources[0]["chunk_id"] == chunk_id
    assert response.metadata["knowledge_bases_found"] == 1
    assert response.metadata["collections_found"] == 1
    assert response.metadata["chunks_retrieved"] == 1
    assert response.metadata["chunks_used"] == 1
    
    # Verify service calls
    mock_retrieval_service.retrieve_relevant_chunks.assert_called_once_with(
        query="Test query",
        collection_ids=[collection_id],
        top_k=5
    )
    
    mock_llm_integration_service.enrich_prompt.assert_called_once_with(
        original_prompt="Original prompt",
        relevant_chunks=chunks,
        max_tokens=4000
    )
    
    mock_retrieval_service.track_chunk_usage.assert_called_once_with(
        chunk_ids=[chunk_id],
        agent_id="agent-123",
        client_id=client_id
    )


@pytest.mark.asyncio
async def test_agent_query_no_knowledge_bases(
    mock_retrieval_service,
    mock_llm_integration_service,
    mock_db_client
):
    """Test agent query with no knowledge bases."""
    # Mock database responses
    client_id = str(uuid.uuid4())
    mock_db_client.rpc().execute.return_value = MagicMock(data=[])
    
    # Create request
    request = AgentQueryRequest(
        query="Test query",
        client_id=client_id,
        agent_id="agent-123",
        original_prompt="Original prompt",
        max_tokens=4000,
        top_k=5
    )
    
    # Call function with mocks
    with patch('knowledge_base.agent_rag_integration.RetrievalService', return_value=mock_retrieval_service), \
         patch('knowledge_base.agent_rag_integration.LLMIntegrationService', return_value=mock_llm_integration_service), \
         patch('knowledge_base.agent_rag_integration.db.client', mock_db_client):
        
        response = await agent_query(request, user_id="user-123")
    
    # Verify response
    assert isinstance(response, AgentQueryResponse)
    assert response.enriched_prompt == "Original prompt"
    assert len(response.used_sources) == 0
    assert response.metadata["knowledge_bases_found"] == 0
    
    # Verify service calls
    mock_retrieval_service.retrieve_relevant_chunks.assert_not_called()
    mock_llm_integration_service.enrich_prompt.assert_not_called()
    mock_retrieval_service.track_chunk_usage.assert_not_called()


@pytest.mark.asyncio
async def test_agent_query_no_relevant_chunks(
    mock_retrieval_service,
    mock_llm_integration_service,
    mock_db_client
):
    """Test agent query with no relevant chunks."""
    # Mock database responses
    client_id = str(uuid.uuid4())
    kb_id = str(uuid.uuid4())
    collection_id = str(uuid.uuid4())
    
    mock_db_client.rpc().execute.side_effect = [
        # Knowledge bases response
        MagicMock(data=[{'id': kb_id, 'name': 'Test KB'}]),
        # Collections response
        MagicMock(data=[{'id': collection_id, 'name': 'Test Collection'}])
    ]
    
    # Mock retrieval service with no chunks
    mock_retrieval_service.retrieve_relevant_chunks.return_value = []
    
    # Create request
    request = AgentQueryRequest(
        query="Test query",
        client_id=client_id,
        agent_id="agent-123",
        original_prompt="Original prompt",
        max_tokens=4000,
        top_k=5
    )
    
    # Call function with mocks
    with patch('knowledge_base.agent_rag_integration.RetrievalService', return_value=mock_retrieval_service), \
         patch('knowledge_base.agent_rag_integration.LLMIntegrationService', return_value=mock_llm_integration_service), \
         patch('knowledge_base.agent_rag_integration.db.client', mock_db_client):
        
        response = await agent_query(request, user_id="user-123")
    
    # Verify response
    assert isinstance(response, AgentQueryResponse)
    assert response.enriched_prompt == "Original prompt"
    assert len(response.used_sources) == 0
    assert response.metadata["knowledge_bases_found"] == 1
    assert response.metadata["collections_found"] == 1
    assert response.metadata["chunks_retrieved"] == 0
    
    # Verify service calls
    mock_retrieval_service.retrieve_relevant_chunks.assert_called_once()
    mock_llm_integration_service.enrich_prompt.assert_not_called()
    mock_retrieval_service.track_chunk_usage.assert_not_called()