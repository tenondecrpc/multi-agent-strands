# AGENTS.md

Development guidelines for any agent working on this codebase.

## Project Overview

Multi-agent software development system that automates Jira ticket handling. Agents (Architect, Backend, Frontend, QA) are orchestrated via Strands SDK to analyze tickets, generate code, run tests, and create PRs. A human always reviews before merge.

**Status**: Early planning phase. No backend/frontend code exists yet.

## Tech Stack

- **Backend**: FastAPI (Python 3.12+), Strands Agents SDK, SQLAlchemy + asyncpg, python-socketio
- **Frontend**: React + Vite + TypeScript, Socket.IO client, Canvas 2D dashboard
- **Database**: PostgreSQL 16
- **LLM**: MiniMax M2.7 via OpenAI-compatible API (Strands `OpenAIModel` provider)
- **MCP**: `mcp-atlassian` (Jira), `github-mcp-server` (GitHub)
- **Infrastructure**: Docker Compose

## Commands

### Backend (`backend/`)
```bash
uv pip install -r requirements.txt          # Install deps
uvicorn main:app --reload --port 8000       # Dev server
pytest                                       # All tests
pytest tests/test_file.py::test_name        # Single test
ruff check . && ruff format .               # Lint + format
mypy .                                       # Type check
```

### Frontend (`frontend/`)
```bash
npm install && npm run dev                   # Install + dev server
npm test                                     # All tests
npm run lint && npx tsc --noEmit            # Lint + type check
```

### Docker
```bash
docker compose up -d                         # Start all
docker compose down                          # Stop all
docker compose build --no-cache              # Rebuild
```

## Code Style & Conventions

- **No comments** unless explicitly requested
- **All communication in English** (commits, PRs, comments, chat)
- Python: `snake_case` functions/vars, `PascalCase` classes, type annotations everywhere
- TypeScript: `PascalCase` components, `camelCase` hooks/utils, interfaces for props
- Ruff for Python, ESLint for TypeScript
- Imperative mood for git commits ("Add feature" not "Added feature")
- Always use official CLIs for project scaffolding (`npm create vite@latest`, `docker init`, cookiecutters). Manual file creation only when extending existing projects or writing business logic.
- Always verify changes: run tests and lint before considering work complete

## Project Structure

```
multi-agent-strands/
├── frontend/src/
│   ├── components/       # Reusable UI components
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components
│   ├── services/         # API services
│   └── types/            # TypeScript types
│
├── backend/app/
│   ├── api/              # API routes (sessions, tickets, agents)
│   ├── core/             # Celery, config, event bus, logging, task queue
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic (agent_manager, ticket_pipeline)
│   ├── agents/           # Strands agent definitions
│   └── mcp/              # MCP client integrations
├── backend/migrations/   # Alembic migrations
├── backend/tests/
│
├── openspec/             # OpenSpec change artifacts
└── docker-compose.yml
```

## Database Schema

PostgreSQL tables:

| Table | Key Columns |
|-------|-------------|
| `ticket_states` | stage, assigned_agent, context_window (JSON), artifacts (JSON), handoff_history (JSON) |
| `agent_sessions` | session_id, ticket_id, agent_type, status, current_task, result (JSON), error, retry_count |
| `agent_events` | Agent event log |
| `events` | event_type, ticket_id, agent_id, payload (JSON), timestamp |

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://agent:agent_local@db:5432/multi_agent
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_MAX_ATTEMPTS=3
CELERY_INITIAL_WAIT=5
CELERY_MAX_WAIT=60
CELERY_MULTIPLIER=2
LLM_API_KEY=
JIRA_URL=
JIRA_API_TOKEN=
JIRA_EMAIL=
GITHUB_TOKEN=
VITE_SOCKET_URL=http://localhost:8000
EVENT_RETENTION_LIMIT=1000
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
```

## Backend Architecture

### Task Queue (Celery + Redis)

- Config: `backend/app/core/celery.py`, Tasks: `backend/app/core/task_queue.py`
- Status: PENDING, RUNNING, COMPLETED, FAILED, RETRY
- Priority: LOW (0), NORMAL (1), HIGH (2), CRITICAL (3)

### Event Bus

In-memory event bus with SSE subscriptions. Event types: `TICKET_RECEIVED`, `TICKET_UPDATED`, `TICKET_STAGE_CHANGED`, `AGENT_STARTED`, `AGENT_COMPLETED`, `AGENT_FAILED`, `AGENT_HANDOFF`, `ARTIFACT_CREATED`, `COMMENT_ADDED`

### Ticket Pipeline

```
NEW → TRIAGED → IN_ANALYSIS → IN_DEVELOPMENT → IN_REVIEW → IN_TESTING → DONE
         ↓           ↓             ↓               ↓            ↓
      BLOCKED ←────────────────────────────────────────────────────
```

### Agent Manager

Orchestrates multi-agent sessions with handoffs between agent types.

### Strands Agent Tools

`file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`

MCP integrations: `mcp-atlassian` (Jira), `github-mcp-server` (GitHub)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tickets/{ticket_id}/process` | POST | Queue ticket for processing |
| `/tickets/{ticket_id}/stage` | POST | Transition ticket stage |
| `/tickets/{ticket_id}/state` | GET | Get ticket state |
| `/tickets/events/{ticket_id}/stream` | GET | SSE stream for ticket events |
| `/sessions` | POST | Create agent session |
| `/sessions/{session_id}/execute` | POST | Execute agent (streaming) |
| `/sessions/{session_id}/handoff` | POST | Hand off to another agent |
| `/sessions/{session_id}` | GET | Get session info |
| `/sessions/{session_id}` | DELETE | Cleanup session |

## Testing

- Backend: `pytest` + `pytest-asyncio`, mock external services (LLM, MCP, database)
- Frontend: Vitest + React Testing Library, mock API with MSW
