"""
Tests for the knowledge base API endpoints.

This module contains tests for the knowledge base API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.rag.models.api import KnowledgeBaseCreate, KnowledgeBaseUpdate


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_get_current_user_id():
    """Mock the get_current_user_id dependency."""
    with patch("app.rag.api_knowledge_base.get_current_user_id") as mock:
        mock.return_value = "test-user-id"
        yield mock


@pytest.fixture
def mock_is_feature_enabled():
    """Mock the is_feature_enabled function."""
    with patch("app.rag.api_knowledge_base.is_feature_enabled") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_knowledge_base_repository():
    """Mock the KnowledgeBaseRepository."""
    with patch("app.rag.api_knowledge_base.KnowledgeBaseRepository") as mock:
        repository_instance = AsyncMock()
        mock.return_value = repository_instance
        yield repository_instance


def test_list_knowledge_bases(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test listing knowledge bases."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_client_id.return_value = [
        {
            "id": kb_id,
            "name": "Test KB",
            "description": "Test description",
            "client_id": "test-user-id",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "collection_count": 2,
            "document_count": 5,
            "total_chunks": 20
        }
    ]
    
    # Make request
    response = client.get("/api/rag/bases")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == kb_id
    assert data[0]["name"] == "Test KB"
    assert data[0]["collection_count"] == 2
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_client_id.assert_called_once_with("test-user-id")


def test_create_knowledge_base(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test creating a knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.create.return_value = {
        "id": kb_id,
        "name": "New KB",
        "description": "New description",
        "client_id": "test-client-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    
    # Make request
    response = client.post(
        "/api/rag/bases",
        json={
            "name": "New KB",
            "description": "New description",
            "client_id": "test-client-id"
        }
    )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == kb_id
    assert data["name"] == "New KB"
    assert data["description"] == "New description"
    
    # Check that the repository method was called
    mock_knowledge_base_repository.create.assert_called_once_with(
        name="New KB",
        client_id="test-client-id",
        description="New description"
    )


def test_get_knowledge_base(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test getting a knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "description": "Test description",
        "client_id": "test-user-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "collection_count": 2,
        "document_count": 5,
        "total_chunks": 20
    }
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == kb_id
    assert data["name"] == "Test KB"
    assert data["collection_count"] == 2
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_get_knowledge_base_not_found(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test getting a non-existent knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_id.side_effect = ValueError("Knowledge base not found")
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}")
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_get_knowledge_base_forbidden(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test getting a knowledge base that belongs to another client."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "description": "Test description",
        "client_id": "another-client-id",  # Different from test-user-id
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}")
    
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_update_knowledge_base(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test updating a knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "description": "Test description",
        "client_id": "test-user-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_knowledge_base_repository.update.return_value = {
        "id": kb_id,
        "name": "Updated KB",
        "description": "Updated description",
        "client_id": "test-user-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-02T00:00:00",
        "collection_count": 2,
        "document_count": 5,
        "total_chunks": 20
    }
    
    # Make request
    response = client.put(
        f"/api/rag/bases/{kb_id}",
        json={
            "name": "Updated KB",
            "description": "Updated description"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == kb_id
    assert data["name"] == "Updated KB"
    assert data["description"] == "Updated description"
    
    # Check that the repository methods were called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_knowledge_base_repository.update.assert_called_once_with(
        knowledge_base_id=kb_id,
        name="Updated KB",
        description="Updated description"
    )


def test_delete_knowledge_base(client, mock_get_current_user_id, mock_is_feature_enabled, mock_knowledge_base_repository):
    """Test deleting a knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "description": "Test description",
        "client_id": "test-user-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_knowledge_base_repository.delete.return_value = True
    
    # Make request
    response = client.delete(f"/api/rag/bases/{kb_id}")
    
    # Check response
    assert response.status_code == 204
    assert response.content == b''
    
    # Check that the repository methods were called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_knowledge_base_repository.delete.assert_called_once_with(kb_id)


def test_feature_disabled(client, mock_get_current_user_id, mock_is_feature_enabled):
    """Test endpoints when the RAG feature is disabled."""
    # Mock feature disabled
    mock_is_feature_enabled.return_value = False
    
    # Test all endpoints
    endpoints = [
        ("GET", "/api/rag/bases"),
        ("POST", "/api/rag/bases"),
        ("GET", f"/api/rag/bases/{uuid4()}"),
        ("PUT", f"/api/rag/bases/{uuid4()}"),
        ("DELETE", f"/api/rag/bases/{uuid4()}")
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={"name": "Test", "client_id": "test"})
        elif method == "PUT":
            response = client.put(endpoint, json={"name": "Test"})
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        # Check response
        assert response.status_code == 403
        data = response.json()
        assert "not available" in data["detail"]