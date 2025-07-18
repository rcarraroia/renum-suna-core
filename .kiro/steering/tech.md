# Suna Technical Stack

## Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Message Queue**: RabbitMQ
- **Cache**: Redis
- **Background Processing**: Dramatiq
- **LLM Integration**: LiteLLM (supports Anthropic, OpenAI, Groq, OpenRouter, AWS Bedrock)
- **Agent Execution**: Daytona
- **Job Processing**: QStash
- **Monitoring**: Sentry

## Frontend

- **Framework**: Next.js 15
- **UI Library**: React 18
- **Styling**: TailwindCSS 4
- **State Management**: Zustand, React Query
- **UI Components**: Radix UI
- **Form Handling**: React Hook Form
- **Validation**: Zod
- **PDF Handling**: React PDF

## Infrastructure

- **Containerization**: Docker
- **Web Scraping**: Firecrawl
- **Search**: Tavily
- **Browser Automation**: Playwright
- **Package Management**: uv (Python), npm (JavaScript)

## Common Commands

### Development Setup

```bash
# Clone repository
git clone https://github.com/kortix-ai/suna.git
cd suna

# Run setup wizard
python setup.py
```

### Docker Deployment

```bash
# Start all services
python start.py
# or
docker compose up -d

# Stop all services
python start.py
# or
docker compose down
```

### Manual Development

```bash
# Start required services
docker compose up redis rabbitmq -d

# Start backend (in one terminal)
cd backend
uv run api.py

# Start worker (in another terminal)
cd backend
uv run dramatiq run_agent_background

# Start frontend (in another terminal)
cd frontend
npm run dev
```

### Testing

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm run test
```

### Environment Configuration

- Backend: `backend/.env`
- Frontend: `frontend/.env.local`