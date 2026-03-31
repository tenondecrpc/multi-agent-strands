# 2. Tech Stack (MVP) ✅

## Frontend
- **React + Vite + TypeScript**
- **Socket.IO client** for real-time events
- **Canvas 2D (SVG + CSS animations)** for agent dashboard

## Backend
- **FastAPI (Python 3.12+)**
- **Strands Agents SDK** — multi-agent orchestration
- **strands_tools** — native tools: `file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`
- **MCP clients** — GitHub (`github-mcp-server`) as agent tools (future)
- **Pydantic** — data validation
- **python-socketio** — Socket.IO server
- **SQLAlchemy + asyncpg** — ORM for PostgreSQL

## LLM
- **MiniMax M2.7** via OpenAI-compatible API, two providers interchangeably:
  - `https://api.minimax.io/v1` (MiniMax official)
  - `https://openrouter.ai/minimax/minimax-m2.7` (OpenRouter)
- Integration with Strands via `OpenAIModel` provider (no custom provider needed)

## Database
- **PostgreSQL 16** — both locally (Docker) and in production (any provider: RDS, Cloud SQL, self-hosted, etc.)

## Environment (Docker Compose)

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌──────────┐  ┌──────────────────────────────────────┐ │
│  │PostgreSQL│  │ FastAPI + Strands SDK                 │ │
│  │  :5432   │  │   ├── Jira polling (direct API)      │ │
│  └──────────┘  │   ├── MCP: github-mcp-server (future)│ │
│       ↑        │   ├── strands_tools (file/shell/edit)│ │
│       └────────│   └── Socket.IO server                │ │
│                └──────────┬───────────────────────────┘ │
│                           ↓                              │
│                    MiniMax API (external)                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ React Dev Server (Vite) ← Socket.IO client       │   │
│  │   :5173                                           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: multi_agent
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent_local
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://agent:agent_local@db:5432/multi_agent
      LLM_API_KEY: ${LLM_API_KEY}
      JIRA_URL: ${JIRA_URL}
      JIRA_API_TOKEN: ${JIRA_API_TOKEN}
      JIRA_EMAIL: ${JIRA_EMAIL}
      JIRA_POLL_INTERVAL_MINUTES: ${JIRA_POLL_INTERVAL_MINUTES:-5}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    depends_on:
      - db
    volumes:
      - ./workspaces:/app/workspaces  # directory where agents write code

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_SOCKET_URL: http://localhost:8000

volumes:
  pgdata:
```

## Production

The same `docker-compose.yml` works in production. The stack is cloud-agnostic — can be deployed to any provider that supports Docker:

| Option | How |
|---|---|
| **VPS / bare metal** | `docker compose up -d` directly |
| **AWS** | ECS Fargate + RDS PostgreSQL |
| **GCP** | Cloud Run + Cloud SQL |
| **Azure** | Container Apps + Azure Database for PostgreSQL |
| **Railway / Render** | Direct deploy from Docker Compose |

For production, add:
- **Reverse proxy** (Nginx/Caddy) with TLS
- **Secrets management** (env vars injected by provider, not in `.env`)
- **Persistent volume** for `/app/workspaces`
- **Managed PostgreSQL** (or same container with persistent volume)
