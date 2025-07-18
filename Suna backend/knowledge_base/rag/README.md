# RAG Module for Renum Platform

## Overview

The RAG (Retrieval-Augmented Generation) module provides functionality for creating and managing knowledge bases, processing documents from various sources, and retrieving relevant information to enhance LLM responses.

## Features

- Create and manage knowledge bases and collections
- Process documents from files, URLs, and raw text
- Generate embeddings for document chunks
- Retrieve relevant information based on queries
- Enrich prompts with context from knowledge bases
- Track usage and gather feedback on relevance
- **Agent Integration**: Seamless integration with Renum platform agents

## Architecture

The RAG module follows a layered architecture:

1. **API Layer**: FastAPI endpoints for client communication
2. **Service Layer**: Business logic implementation
3. **Repository Layer**: Data access and persistence
4. **Model Layer**: Data models and entities

## Components

### Models

- `entities.py`: Core domain entities
- `api.py`: Request and response models for the API

### Repositories

- `knowledge_base_repository.py`: Data access for knowledge bases
- `collection_repository.py`: Data access for collections
- `document_repository.py`: Data access for documents

### Services

- `ingestion_service.py`: Processing and ingestion of documents
- `chunking_service.py`: Text chunking strategies
- `embedding_service.py`: Generation and management of embeddings
- `retrieval_service.py`: Retrieval of relevant information
- `llm_integration_service.py`: Integration with LLMs

### API

- `api.py`: FastAPI endpoints for the RAG module
- `agent_rag_integration.py`: Integration endpoints for Renum platform agents

### Utils

- `sql_scripts.py`: SQL scripts for database setup
- `agent_integration_sql.py`: SQL functions for agent integration
- `db_init.py`: Database initialization

## Database Schema

- `knowledge_bases`: Knowledge base metadata
- `knowledge_collections`: Collections within knowledge bases
- `documents`: Document metadata
- `document_chunks`: Document chunks and content
- `document_versions`: Document version history
- `document_usage_stats`: Usage statistics
- `retrieval_feedback`: User feedback on relevance
- `processing_jobs`: Document processing jobs
- `client_plans`: Client subscription plans and limits

## Agent Integration

The RAG module provides seamless integration with Renum platform agents through dedicated endpoints:

- `POST /api/knowledge-base/agent-rag/query`: Enrich agent prompts with relevant knowledge
- `POST /api/knowledge-base/agent-rag/feedback`: Submit feedback on retrieved chunks

For detailed information on agent integration, see [Agent Integration Documentation](docs/agent_integration.md).

## Usage

### Creating a Knowledge Base

```python
from knowledge_base.rag.repositories.knowledge_base_repository import KnowledgeBaseRepository

async def create_kb():
    repo = KnowledgeBaseRepository()
    kb = await repo.create(
        name="My Knowledge Base",
        description="My personal knowledge base",
        client_id="client-123"
    )
    return kb
```

### Processing a Document

```python
from knowledge_base.rag.services.ingestion_service import IngestionCoordinator

async def process_document():
    coordinator = IngestionCoordinator()
    job_id = await coordinator.process_document(
        source_type="file",
        collection_id="collection-123",
        content=file_bytes,
        metadata={
            "name": "document.pdf",
            "file_type": "application/pdf"
        }
    )
    return job_id
```

### Retrieving Relevant Information

```python
from knowledge_base.rag.services.retrieval_service import RetrievalService

async def retrieve_info():
    service = RetrievalService()
    chunks, metadata = await service.retrieve_relevant_chunks(
        query="What is RAG?",
        collection_ids=["collection-123"],
        top_k=5
    )
    return chunks
```

### Enriching a Prompt with Agent Integration

```python
import httpx

async def enrich_prompt_with_rag(query, client_id, agent_id, original_prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/knowledge-base/agent-rag/query",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "client_id": client_id,
                "agent_id": agent_id,
                "original_prompt": original_prompt,
                "max_tokens": 4000,
                "top_k": 5
            }
        )
        result = response.json()
        return result["enriched_prompt"]
```

## Testing

The module includes comprehensive tests for all components:

```bash
pytest backend/knowledge_base/rag/tests/
```

## Documentation

- [Agent Integration](docs/agent_integration.md): Detailed guide on integrating agents with RAG
- [Integration Overview](docs/INTEGRATION.md): Overview of the RAG module integration with Renum platform

## Future Improvements

- Support for more document formats (presentations, spreadsheets)
- Advanced chunking strategies (semantic chunking)
- Multilingual support
- Continuous learning from feedback
- Integration with more vector databases