# Suna Project Structure

## Root Directory

- `.github/`: GitHub workflows and configuration
- `.kiro/`: Kiro AI assistant configuration
- `.vscode/`: VS Code editor settings
- `backend/`: Python backend services
- `docs/`: Documentation files
- `frontend/`: Next.js frontend application
- `docker-compose.yaml`: Main Docker Compose configuration
- `setup.py`: Setup wizard script
- `start.py`: Service management script

## Backend Structure

- `backend/agent/`: Agent implementation and logic
- `backend/agentpress/`: Thread management system
- `backend/api.py`: Main FastAPI application entry point
- `backend/mcp_service/`: Model Context Protocol service
- `backend/knowledge_base/`: Knowledge base implementation
- `backend/pipedream/`: Pipedream integration
- `backend/sandbox/`: Isolated execution environment
- `backend/services/`: Core services (Redis, Supabase, etc.)
- `backend/supabase/`: Supabase database integration
- `backend/triggers/`: Event trigger system
- `backend/utils/`: Utility functions and helpers

## Frontend Structure

- `frontend/public/`: Static assets
- `frontend/src/`: Source code
  - `app/`: Next.js app router pages
  - `components/`: React components
  - `lib/`: Utility libraries
  - `hooks/`: React hooks
  - `styles/`: CSS and styling

## Configuration Files

- `backend/.env`: Backend environment variables
- `frontend/.env.local`: Frontend environment variables
- `.kilocode/mcp.json`: MCP configuration
- `mise.toml`: Development environment configuration

## Architecture Pattern

Suna follows a microservices architecture with:

1. **API Layer**: FastAPI endpoints for client communication
2. **Service Layer**: Business logic implementation
3. **Agent Layer**: AI agent implementation and execution
4. **Data Layer**: Supabase database integration
5. **Worker Layer**: Background task processing with Dramatiq

## Development Workflow

1. Backend changes should include appropriate tests
2. Frontend follows component-based architecture
3. Docker containers are used for consistent deployment
4. Environment variables control configuration across environments
5. Supabase handles database schema and migrations