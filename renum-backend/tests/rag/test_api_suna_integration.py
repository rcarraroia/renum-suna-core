"""
Tests for the Suna Core integration API endpoints.

This module contains tests for the Suna Core integration API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_get_current_user_id():
    """Mock the get_current_user_id dependency."""
    with patch("app.rag.api_suna_integration.get_current_user_id") as mock:
        mock.return_value = "test-user-id"
        yield mock


@pytest.fixture
def mock_is_feature_enabled():
    """Mock the is_feature_enabled function."""
    with patch("app.rag.api_suna_integration.is_feature_enabled") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_suna_integration_service():
    """Mock the SunaIntegrationService."""
    with patch("app.rag.api_suna_integration.SunaIntegrationService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance


def test_enrich_prompt_for_suna(client, mock_get_current_user_id, mock_is_feature_enabled, mock_suna_integration_service):
    """Test enriching a prompt for Suna Core."""
    # Mock data
    mock_suna_integration_service.enrich_prompt_for_suna.return_value = {
        "enriched_prompt": "Enriched prompt with context",
        "used_sources": [
            {
                "chunk_id": "chunk-id",
                "document_id": "document-id",
                "document_name": "Test Document",
                "collection_id": "collection-id",
                "collection_name": "Test Collection",
                "similarity": 0.95,
                "content_preview": "This is a test chunk"
            }
        ],
        "metadata": {
            "knowledge_bases_found": 1,
            "collections_found": 1,
            "chunks_retrieved": 5,
            "chunks_used": 1
        }
    }
    
    # Make request
    response = client.post(
        "/api/rag/suna/enrich",
        json={
            "query": "What is RAG?",
            "client_id": "test-client-id",
            "agent_id": "test-agent-id",
            "original_prompt": "Tell me about RAG",
            "max_tokens": 4000,
            "top_k": 5
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["enriched_prompt"] == "Enriched prompt with context"
    assert len(data["used_sources"]) == 1
    assert data["metadata"]["chunks_used"] == 1
    
    # Check that the service method was called
    mock_suna_integration_service.enrich_prompt_for_suna.assert_called_once_with(
        query="What is RAG?",
        client_id="test-client-id",
        agent_id="test-agent-id",
        original_prompt="Tell me about RAG",
        max_tokens=4000,
        top_k=5
    )


def test_execute_suna_with_rag(client, mock_get_current_user_id, mock_is_feature_enabled, mock_suna_integration_service):
    """Test executing a Suna agent with RAG."""
    # Mock data
    mock_suna_integration_service.send_enriched_prompt_to_suna.return_value = {
        "response": "This is a response from Suna Core",
        "execution_time": 1.5,
        "rag_metadata": {
            "knowledge_bases_found": 1,
            "collections_found": 1,
            "chunks_retrieved": 5,
            "chunks_used": 1
        },
        "rag_sources": [
            {
                "chunk_id": "chunk-id",
                "document_id": "document-id",
                "document_name": "Test Document",
                "collection_id": "collection-id",
                "collection_name": "Test Collection",
                "similarity": 0.95,
                "content_preview": "This is a test chunk"
            }
        ]
    }
    
    # Make request
    response = client.post(
        "/api/rag/suna/execute",
        json={
            "query": "What is RAG?",
            "client_id": "test-client-id",
            "agent_id": "test-agent-id",
            "original_prompt": "Tell me about RAG",
            "max_tokens": 4000,
            "top_k": 5
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "This is a response from Suna Core"
    assert "rag_metadata" in data
    assert "rag_sources" in data
    
    # Check that the service method was called
    mock_suna_integration_service.send_enriched_prompt_to_suna.assert_called_once_with(
        query="What is RAG?",
        client_id="test-client-id",
        agent_id="test-agent-id",
        original_prompt="Tell me about RAG",
        max_tokens=4000,
        top_k=5
    )


def test_feature_disabled(client, mock_get_current_user_id, mock_is_feature_enabled):
    """Test endpoints when the RAG feature is disabled."""
    # Mock feature disabled
    mock_is_feature_enabled.return_value = False
    
    # Test all endpoints
    endpoints = [
        "/api/rag/suna/enrich",
        "/api/rag/suna/execute"
    ]
    
    for endpoint in endpoints:
        response = client.post(
            endpoint,
            json={
                "query": "What is RAG?",
                "client_id": "test-client-id",
                "agent_id": "test-agent-id",
                "original_prompt": "Tell me about RAG",
                "max_tokens": 4000,
                "top_k": 5
            }
        )
        
        # Check response
        assert response.status_code == 403
        data = response.json()
        assert "not available" in data["detail"]