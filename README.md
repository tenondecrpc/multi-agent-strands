# Multi-Agent Strands

![Strands Agents](strands-agents.png)

Multi-agent software development system that automates Jira ticket handling using Strands Agents SDK.

## Architecture

![Architecture Diagram](docs/architecture/architecture-diagram.png)

The system consists of three main components:
- **Frontend**: React + Vite + TypeScript for the user interface
- **Backend**: FastAPI + Strands Agents SDK for orchestration and business logic
- **Database**: PostgreSQL for persistent storage of ticket states, agent sessions, and events

### Agent Architecture

![Agent Diagrams](docs/architecture/agent-diagrams.png)

Detailed diagrams for each agent:
- **Orchestrator Agent**: Manages Jira integration, delegates tasks to sub-agents, coordinates workflow
- **Backend Agent**: Implements FastAPI endpoints, Pydantic models, SQLAlchemy models
- **Frontend Agent**: Creates React components, pages, TypeScript code
- **QA Agent**: Writes and executes tests (pytest, Vitest), creates physical test files

## Quick Start

### Prerequisites

- **Node.js** 18+ (frontend)
- **Python** 3.12+ (backend)
- **PostgreSQL** 15+ (local without Docker)
- **Docker Compose** (with Docker)

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `LLM_API_KEY` - MiniMax API key for LLM
- `JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL` - Jira credentials
- `GITHUB_TOKEN` - GitHub token

---

## With Docker (Recommended)

### Start All Services

```bash
docker compose up -d   # -d runs containers in background (detach)
```

Services:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

### Verify Services

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Frontend (should show the app)
curl http://localhost:3000

# Check container status
docker compose ps
```

### Database Migrations

Migrations are **not automatic** - you must run them manually after starting containers:

```bash
# Run pending migrations (required after first start or model changes)
docker compose exec backend alembic upgrade head

# Check current migration status
docker compose exec backend alembic current
docker compose exec backend alembic history

# Verify tables were created correctly
docker compose exec db psql -U agent -d multi_agent -c "\dt"
```

### View Logs

```bash
# All logs ( Ctrl+C to exit)
docker compose logs -f backend
docker compose logs -f frontend

# Last 50 lines
docker compose logs --tail=50 backend

# Last errors only
docker compose logs --tail=50 backend | grep -i "error\|exception\|traceback"

# Logs since last N minutes
docker compose logs --since=10m backend
```

### Stop Services

```bash
# Stop containers (preserves data)
docker compose down

# Stop and remove everything (including data volumes)
docker compose down -v
```

### Restart / Clean Slate

```bash
# Full restart with clean state (removes volumes + database + reinitializes)
docker compose down -v && docker compose up -d && sleep 5 && docker compose exec backend alembic upgrade head
```

### Container Management

```bash
# Restart a single service
docker compose restart backend
docker compose restart frontend

# View resource usage
docker stats

# Access container shell (for debugging)
docker compose exec backend sh
docker compose exec db psql -U agent -d multi_agent

# Pause/unpause services
docker compose pause
docker compose unpause

# View container logs in real-time (all services)
docker compose logs -f

# Check container health status
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

---

## Without Docker

### Database Setup

Create PostgreSQL database:

```sql
CREATE USER agent WITH PASSWORD 'agent_local';
CREATE DATABASE multi_agent OWNER agent;
```

Or via command line:

```bash
psql -U postgres -c "CREATE USER agent WITH PASSWORD 'agent_local';"
psql -U postgres -c "CREATE DATABASE multi_agent OWNER agent;"
```

### Database Migrations

This project uses Alembic for database migrations.

```bash
cd backend

# Run all pending migrations
alembic upgrade head

# Check current migration status
alembic current
alembic history

# Generate a new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"

# Rollback last migration
alembic downgrade -1
```

Environment variables:
- `DATABASE_URL` - Connection string (default: `postgresql+asyncpg://agent:agent_local@localhost:5432/multi_agent`)

### Backend

**Important:** Always use a project-specific virtual environment (not global Python).

```bash
cd backend

# Create virtual environment (local to project)
python -m venv .venv

# Activate (run this each time before working on the project)
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Install new dependency (then update requirements.txt)
pip install nueva-libreria
pip freeze > requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# When done, exit the virtual environment
deactivate
```

API available at http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

App available at http://localhost:3000

### Docker Development (with pending changes)

```bash
# Frontend only changed (no new deps) → restart frontend
docker compose restart frontend

# Frontend changed + npm install → rebuild frontend
docker compose up -d --build frontend

# Backend only changed → restart backend
docker compose restart backend

# Backend changed + pip install → rebuild backend + run migrations
docker compose up -d --build backend && docker compose exec backend alembic upgrade head

# Both frontend + backend changed (no new deps) → rebuild both
docker compose up -d --build

# Both changed + new npm/pip deps → full rebuild both
docker compose down && docker compose up -d --build && docker compose exec backend alembic upgrade head

# Force rebuild without cache (fixes stale code issues)
docker compose up -d --build --no-cache frontend   # only frontend
docker compose up -d --build --no-cache backend    # only backend
docker compose up -d --build --no-cache            # all services
```

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

---

## Project Structure

```
multi-agent-strands/
├── frontend/          # React + Vite + TypeScript
├── backend/           # FastAPI + Strands Agents SDK
├── docker-compose.yml
├── .env.example
└── openspec/          # Specification-driven development
```

---

## Development Commands

### Backend

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Dev server |
| `pytest` | Run tests |
| `ruff check . && ruff format .` | Lint & format |
| `mypy .` | Type check |

### Frontend

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm test` | Run tests |
| `npm run lint` | Lint |
| `npx tsc --noEmit` | Type check |

---

## OpenSpec Workflow

This project uses OpenSpec for specification-driven development:

```bash
# Explore ideas
/opsx:explore

# Propose new change
/opsx:propose

# Implement tasks
/opsx:apply

# Archive completed change
/opsx:archive
```

---

## Debugging Jira Integration

### Test Jira API Directly

Get an API token from: https://id.atlassian.com/manage-profile/security/api-tokens

```bash
# Search tickets by status
curl -s -X GET \
  -H "Authorization: Basic $(echo -n 'YOUR_EMAIL:YOUR_API_TOKEN' | base64)" \
  -H "Accept: application/json" \
  "https://YOUR_DOMAIN.atlassian.net/rest/api/3/search/jql?jql=status%20=%20%27To%20Do%27&maxResults=5&fields=key,summary,status"

# Get single ticket
curl -s -X GET \
  -H "Authorization: Basic $(echo -n 'YOUR_EMAIL:YOUR_API_TOKEN' | base64)" \
  -H "Accept: application/json" \
  "https://YOUR_DOMAIN.atlassian.net/rest/api/3/issue/TICKET-KEY"
```

### Check MCP Connection

The MCP server uses `uvx mcp-atlassian`. If connection fails, verify:
1. `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` are set in `.env`
2. API token is valid and not expired
3. Email matches the Atlassian account
