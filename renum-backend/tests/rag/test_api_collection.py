"""
Tests for the collection API endpoints.

This module contains tests for the collection API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.rag.models.api import CollectionCreate, CollectionUpdate


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_get_current_user_id():
    """Mock the get_current_user_id dependency."""
    with patch("app.rag.api_collection.get_current_user_id") as mock:
        mock.return_value = "test-user-id"
        yield mock


@pytest.fixture
def mock_is_feature_enabled():
    """Mock the is_feature_enabled function."""
    with patch("app.rag.api_collection.is_feature_enabled") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_collection_repository():
    """Mock the CollectionRepository."""
    with patch("app.rag.api_collection.CollectionRepository") as mock:
        repository_instance = AsyncMock()
        mock.return_value = repository_instance
        yield repository_instance


@pytest.fixture
def mock_knowledge_base_repository():
    """Mock the KnowledgeBaseRepository."""
    with patch("app.rag.api_collection.KnowledgeBaseRepository") as mock:
        repository_instance = AsyncMock()
        mock.return_value = repository_instance
        yield repository_instance


def test_list_collections(client, mock_get_current_user_id, mock_is_feature_enabled, 
                         mock_collection_repository, mock_knowledge_base_repository):
    """Test listing collections."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "test-user-id"
    }
    
    # Mock collection repository
    mock_collection_repository.get_by_knowledge_base_id.return_value = [
        {
            "id": collection_id,
            "knowledge_base_id": kb_id,
            "name": "Test Collection",
            "description": "Test description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    ]
    mock_collection_repository.get_document_count.return_value = 5
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}/collections")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == collection_id
    assert data[0]["name"] == "Test Collection"
    assert data[0]["document_count"] == 5
    
    # Check that the repository methods were called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_collection_repository.get_by_knowledge_base_id.assert_called_once_with(kb_id)
    mock_collection_repository.get_document_count.assert_called_once_with(collection_id)


def test_list_collections_kb_not_found(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                      mock_knowledge_base_repository):
    """Test listing collections with non-existent knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.side_effect = ValueError("Knowledge base not found")
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}/collections")
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_list_collections_forbidden(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                   mock_knowledge_base_repository):
    """Test listing collections with forbidden knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "another-client-id"  # Different from test-user-id
    }
    
    # Make request
    response = client.get(f"/api/rag/bases/{kb_id}/collections")
    
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_create_collection(client, mock_get_current_user_id, mock_is_feature_enabled, 
                          mock_collection_repository, mock_knowledge_base_repository):
    """Test creating a collection."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "test-user-id"
    }
    
    # Mock collection repository
    mock_collection_repository.create.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "New Collection",
        "description": "New description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    
    # Make request
    response = client.post(
        "/api/rag/collections",
        json={
            "knowledge_base_id": kb_id,
            "name": "New Collection",
            "description": "New description"
        }
    )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "New Collection"
    assert data["description"] == "New description"
    
    # Check that the repository methods were called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_collection_repository.create.assert_called_once_with(
        knowledge_base_id=kb_id,
        name="New Collection",
        description="New description"
    )


def test_create_collection_kb_not_found(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                       mock_knowledge_base_repository):
    """Test creating a collection with non-existent knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.side_effect = ValueError("Knowledge base not found")
    
    # Make request
    response = client.post(
        "/api/rag/collections",
        json={
            "knowledge_base_id": kb_id,
            "name": "New Collection",
            "description": "New description"
        }
    )
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_create_collection_forbidden(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                    mock_knowledge_base_repository):
    """Test creating a collection with forbidden knowledge base."""
    # Mock data
    kb_id = str(uuid4())
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "another-client-id"  # Different from test-user-id
    }
    
    # Make request
    response = client.post(
        "/api/rag/collections",
        json={
            "knowledge_base_id": kb_id,
            "name": "New Collection",
            "description": "New description"
        }
    )
    
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"]
    
    # Check that the repository method was called
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_get_collection(client, mock_get_current_user_id, mock_is_feature_enabled, 
                       mock_collection_repository, mock_knowledge_base_repository):
    """Test getting a collection."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock collection repository
    mock_collection_repository.get_by_id.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "Test Collection",
        "description": "Test description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_collection_repository.get_document_count.return_value = 5
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "test-user-id"
    }
    
    # Make request
    response = client.get(f"/api/rag/collections/{collection_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "Test Collection"
    assert data["document_count"] == 5
    
    # Check that the repository methods were called
    mock_collection_repository.get_by_id.assert_called_once_with(collection_id)
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_collection_repository.get_document_count.assert_called_once_with(collection_id)


def test_get_collection_not_found(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                 mock_collection_repository):
    """Test getting a non-existent collection."""
    # Mock data
    collection_id = str(uuid4())
    
    # Mock collection repository
    mock_collection_repository.get_by_id.side_effect = ValueError("Collection not found")
    
    # Make request
    response = client.get(f"/api/rag/collections/{collection_id}")
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    
    # Check that the repository method was called
    mock_collection_repository.get_by_id.assert_called_once_with(collection_id)


def test_get_collection_forbidden(client, mock_get_current_user_id, mock_is_feature_enabled, 
                                 mock_collection_repository, mock_knowledge_base_repository):
    """Test getting a collection that belongs to another client."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock collection repository
    mock_collection_repository.get_by_id.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "Test Collection",
        "description": "Test description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "another-client-id"  # Different from test-user-id
    }
    
    # Make request
    response = client.get(f"/api/rag/collections/{collection_id}")
    
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"]
    
    # Check that the repository methods were called
    mock_collection_repository.get_by_id.assert_called_once_with(collection_id)
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)


def test_update_collection(client, mock_get_current_user_id, mock_is_feature_enabled, 
                          mock_collection_repository, mock_knowledge_base_repository):
    """Test updating a collection."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock collection repository
    mock_collection_repository.get_by_id.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "Test Collection",
        "description": "Test description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_collection_repository.update.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "Updated Collection",
        "description": "Updated description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-02T00:00:00"
    }
    mock_collection_repository.get_document_count.return_value = 5
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "test-user-id"
    }
    
    # Make request
    response = client.put(
        f"/api/rag/collections/{collection_id}",
        json={
            "name": "Updated Collection",
            "description": "Updated description"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "Updated Collection"
    assert data["description"] == "Updated description"
    
    # Check that the repository methods were called
    mock_collection_repository.get_by_id.assert_called_once_with(collection_id)
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_collection_repository.update.assert_called_once_with(
        collection_id=collection_id,
        name="Updated Collection",
        description="Updated description"
    )
    mock_collection_repository.get_document_count.assert_called_once_with(collection_id)


def test_delete_collection(client, mock_get_current_user_id, mock_is_feature_enabled, 
                          mock_collection_repository, mock_knowledge_base_repository):
    """Test deleting a collection."""
    # Mock data
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    # Mock collection repository
    mock_collection_repository.get_by_id.return_value = {
        "id": collection_id,
        "knowledge_base_id": kb_id,
        "name": "Test Collection",
        "description": "Test description",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_collection_repository.delete.return_value = True
    
    # Mock knowledge base repository
    mock_knowledge_base_repository.get_by_id.return_value = {
        "id": kb_id,
        "name": "Test KB",
        "client_id": "test-user-id"
    }
    
    # Make request
    response = client.delete(f"/api/rag/collections/{collection_id}")
    
    # Check response
    assert response.status_code == 204
    assert response.content == b''
    
    # Check that the repository methods were called
    mock_collection_repository.get_by_id.assert_called_once_with(collection_id)
    mock_knowledge_base_repository.get_by_id.assert_called_once_with(kb_id)
    mock_collection_repository.delete.assert_called_once_with(collection_id)


def test_feature_disabled(client, mock_get_current_user_id, mock_is_feature_enabled):
    """Test endpoints when the RAG feature is disabled."""
    # Mock feature disabled
    mock_is_feature_enabled.return_value = False
    
    # Test all endpoints
    kb_id = str(uuid4())
    collection_id = str(uuid4())
    
    endpoints = [
        ("GET", f"/api/rag/bases/{kb_id}/collections"),
        ("POST", "/api/rag/collections"),
        ("GET", f"/api/rag/collections/{collection_id}"),
        ("PUT", f"/api/rag/collections/{collection_id}"),
        ("DELETE", f"/api/rag/collections/{collection_id}")
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={"knowledge_base_id": kb_id, "name": "Test"})
        elif method == "PUT":
            response = client.put(endpoint, json={"name": "Test"})
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        # Check response
        assert response.status_code == 403
        data = response.json()
        assert "not available" in data["detail"]