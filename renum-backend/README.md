# Renum Backend

This is the backend for the Renum Platform, a system for creating and orchestrating AI agents.

## Overview

The Renum Backend provides the following functionality:

- User and client management
- Secure storage of API credentials
- Orchestration of Suna Core instances
- Usage tracking and billing
- APIs for the Renum Builder frontend
- Proxy for external tool calls
- RAG (Retrieval-Augmented Generation) module for memory and context

## Architecture

The Renum Backend follows a modular architecture:

- `app/core`: Core functionality (configuration, database, authentication, etc.)
- `app/rag`: RAG module for memory and context
- `app/users`: User and client management
- `app/agents`: Agent orchestration
- `app/proxy`: Proxy for external tool calls
- `app/billing`: Usage tracking and billing

## RAG Module

The RAG module provides functionality for creating and managing knowledge bases, processing documents from various sources, and retrieving relevant information to enhance LLM responses.

### Features

- Create and manage knowledge bases and collections
- Process documents from files, URLs, and raw text
- Generate embeddings for document chunks
- Retrieve relevant information based on queries
- Enrich prompts with context from knowledge bases
- Track usage and gather feedback on relevance
- Agent integration for seamless access to knowledge

## Getting Started

### Prerequisites

- Python 3.11+
- Supabase account
- Redis (optional, for caching)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Project Structure

```
renum-backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── logger.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── utils/
│   │   └── tests/
│   ├── __init__.py
│   └── main.py
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### Testing

Run tests with pytest:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.