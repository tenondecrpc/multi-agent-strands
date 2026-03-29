# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent software development system that automates Jira ticket handling. Agents (Architect, Backend, Frontend, QA) are orchestrated via Strands SDK to analyze tickets, generate code, run tests, and create PRs. A human always reviews before merge.

**Status**: Early planning phase. No backend/frontend code exists yet. Architecture is defined in `docs/PLAN.md`.

## Tech Stack

- **Backend**: FastAPI (Python 3.12+), Strands Agents SDK, SQLAlchemy + asyncpg, python-socketio
- **Frontend**: React + Vite + TypeScript, Socket.IO client, Canvas 2D dashboard
- **Database**: PostgreSQL 16
- **LLM**: MiniMax M2.7 via OpenAI-compatible API (integrated through Strands `OpenAIModel` provider)
- **MCP integrations**: `mcp-atlassian` (Jira), `github-mcp-server` (GitHub)
- **Infrastructure**: Docker Compose

## Build & Test Commands

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
docker compose up -d                         # Start all services
docker compose down                          # Stop all
docker compose build --no-cache              # Rebuild
```

## Architecture

```
Jira Ticket (read via MCP)
    ↓
Strands SDK Orchestrator Agent
    ├── MCP: Jira (read/update tickets)
    ├── MCP: GitHub (branches, PRs)
    ↓ decomposes ticket
    ┌────┼────┬────┐
    ↓    ↓    ↓    ↓
  Arch  Back Front  QA     ← each uses strands_tools: file_read, file_write, editor, shell
    └────┼────┴────┘
         ↓
  Git Branch + PR → CI → Human Review → Merge
```

Key architectural decisions:
- **Human-in-the-loop**: Generated code never goes directly to production
- **MCP-first**: Jira/GitHub integration via MCP servers, not direct APIs
- **Billing guardrails**: Timeouts, iteration limits, and token budgets per agent to prevent infinite loops
- **Real-time dashboard**: Socket.IO for agent status visualization

## Code Style

- **No comments** unless explicitly requested
- Python: `snake_case` functions/vars, `PascalCase` classes, type annotations everywhere
- TypeScript: `PascalCase` components, `camelCase` hooks/utils, interfaces for props
- Ruff for Python linting/formatting, ESLint for TypeScript
- Imperative mood for git commits (e.g., "Add feature" not "Added feature")

## Communication Standards

- **All communication must be in English** - Include code comments, PR descriptions, commit messages, chat messages, and any other communication
- **No code comments unless explicitly requested by the user** - Code should be self-documenting through meaningful names

## Scaffolding Rule (IMPORTANT)

**Always use official CLIs for project scaffolding and initialization.** Manual file creation is only acceptable when no official CLI exists or when extending an existing project.

| When | Use |
|------|-----|
| New React project | `npm create vite@latest my-app -- --template react-ts` |
| New Python/FastAPI | Use cookiecutters or official templates |
| Docker setup | `docker init` when available |

**When NOT to use CLIs**: Extending existing projects, custom configs, business logic code. See `AGENTS.md` Section 10 for details.

## OpenSpec Workflow (Specification-Driven Development)

This project uses OpenSpec for planning changes. Config at `openspec/config.yaml`, changes tracked in `openspec/changes/`.

1. `/opsx:explore` - Think through ideas before committing
2. `/opsx:propose` - Create change with proposal, design, and tasks
3. `/opsx:apply` - Implement tasks from a change
4. `/opsx:archive` - Finalize completed changes

CLI: `openspec list`, `openspec status --change "<name>"`, `openspec new change "<name>"`

## Environment Variables

Required: `DATABASE_URL`, `MINIMAX_API_KEY`, `JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL`, `GITHUB_TOKEN`, `VITE_SOCKET_URL`
