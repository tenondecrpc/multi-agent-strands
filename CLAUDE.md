# CLAUDE.md

## Project Overview

Multi-agent software development system that automates Jira ticket handling. Agents (Architect, Backend, Frontend, QA) are orchestrated via Strands SDK to analyze tickets, generate code, run tests, and create PRs. A human always reviews before merge.

**Status**: Early planning phase. No backend/frontend code exists yet. Architecture is defined in `docs/PLAN.md`.

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
pytest --cov=. --cov-report=html            # Coverage
ruff check . && ruff format .               # Lint + format
mypy .                                       # Type check
```

### Frontend (`frontend/`)
```bash
npm install                                  # Install deps
npm run dev                                  # Dev server
npm test                                     # All tests
npx vitest run test_file_name               # Single test
npm run lint                                 # Lint
npx tsc --noEmit                            # Type check
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

## OpenSpec Workflow

Config at `openspec/config.yaml`, changes tracked in `openspec/changes/`.

1. `/opsx:explore` - Think through ideas before committing
2. `/opsx:propose` - Create change with proposal, design, and tasks
3. `/opsx:apply` - Implement tasks from a change
4. `/opsx:archive` - Finalize completed changes

CLI: `openspec list`, `openspec status --change "<name>"`, `openspec new change "<name>"`

## Environment Variables

Required: `DATABASE_URL`, `LLM_API_KEY`, `JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL`, `GITHUB_TOKEN`, `VITE_SOCKET_URL`
