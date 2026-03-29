# Multi-Agent Strands

Multi-agent software development system that automates Jira ticket handling using Strands Agents SDK.

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
- `MINIMAX_API_KEY` - MiniMax API key for LLM
- `JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL` - Jira credentials
- `GITHUB_TOKEN` - GitHub token

---

## With Docker (Recommended)

### Start All Services

```bash
docker compose up -d
```

Services:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

### View Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services

```bash
docker compose down
```

### Rebuild (after dependency changes)

```bash
docker compose build --no-cache
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
