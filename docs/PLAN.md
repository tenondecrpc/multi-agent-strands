# Multi-Agent System for Software Development via Jira

## 1. Overview

Multi-agent system that activates automatically when a Jira ticket is created or updated. Specialized software development agents (Architect, Backend, Frontend, QA) analyze the ticket, generate code, run tests, and create a Pull Request. **A human always reviews and approves before merging to production.**

### Main Flow

```
Jira Ticket (polling detects "To Do")
       ↓
Strands SDK Orchestrator Agent
  ├── Jira API (direct polling)
  ├── GitHub MCP (future: create branch, PR)
  ↓ decomposes the ticket
  ┌────┼────┬────────┐
  ↓    ↓    ↓        ↓
Arch  Back  Front    QA
Agent Agent Agent  Agent
  │    (strands_tools: file_read, file_write, editor, shell)
  └────┼────┴────────┘
       ↓ generated code
  Git Branch + Pull Request (via GitHub API)
       ↓
  CI/CD Pipeline
       ↓ automated tests
  Human Review & Approve
       ↓
  Runbook: Validation and Documentation
       ↓
  Merge → Deploy to Prod
```

### Principles

- **Human-in-the-loop**: Generated code NEVER goes directly to production. Always passes through PR + human review.
- **Cost-effective**: MiniMax M2.7 as main LLM via OpenAI-compatible API.
- **Cloud-agnostic**: Docker + PostgreSQL locally and in production. No dependency on specific cloud services.
- **API-first**: Jira integrates via direct REST API; MCP for future tools.
- **Billing guardrails**: Timeouts, iteration limits, and token budgets per agent to avoid infinite loops.
- **Strands tools**: Agents use `strands_tools` (file_read, file_write, editor, shell) to operate on code.
- **Observable**: Real-time 2D Canvas dashboard via Socket.IO.

---

## 2. Tech Stack (MVP) (✅ Completed)

### Frontend
- **React + Vite + TypeScript**
- **Socket.IO client** for real-time events
- **Canvas 2D (SVG + CSS animations)** for agent dashboard

### Backend
- **FastAPI (Python 3.12+)**
- **Strands Agents SDK** — multi-agent orchestration
- **strands_tools** — native tools: `file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`
- **MCP clients** — GitHub (`github-mcp-server`) as agent tools (future)
- **Pydantic** — data validation
- **python-socketio** — Socket.IO server
- **SQLAlchemy + asyncpg** — ORM for PostgreSQL

### LLM
- **MiniMax M2.7** via OpenAI-compatible API, two providers interchangeably:
  - `https://api.minimax.io/v1` (MiniMax official)
  - `https://openrouter.ai/minimax/minimax-m2.7` (OpenRouter)
- Integration with Strands via `OpenAIModel` provider (no custom provider needed)

### Database
- **PostgreSQL 16** — both locally (Docker) and in production (any provider: RDS, Cloud SQL, self-hosted, etc.)

### Environment (Docker Compose)

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
      MINIMAX_API_KEY: ${MINIMAX_API_KEY}
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

### Production

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

---

## 3. Data Model (✅ Completed)

PostgreSQL 16 with async SQLAlchemy.

```sql
-- Pipeline sessions
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    -- started, in_progress, pr_created, error, completed
    pr_url TEXT,
    result TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_ticket ON agent_sessions(ticket_id);

-- Agent events (feed dashboard via Socket.IO)
CREATE TABLE agent_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id),
    agent_id VARCHAR(50) NOT NULL,
    -- architect, backend_agent, frontend_agent, qa_agent
    event_type VARCHAR(30) NOT NULL,
    -- state_change, log, error, task_assigned, task_completed
    previous_state VARCHAR(20),
    new_state VARCHAR(20),
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_session ON agent_events(session_id, created_at);
```

#### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="started")
    pr_url = Column(Text)
    result = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    events = relationship("AgentEvent", back_populates="session")

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id"), nullable=False)
    agent_id = Column(String(50), nullable=False)
    event_type = Column(String(30), nullable=False)
    previous_state = Column(String(20))
    new_state = Column(String(20))
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("AgentSession", back_populates="events")
```

---

## 4. Jira Integration via API Polling (✅ Completed)

Jira polling uses **direct REST API** for better reliability. MCP (`mcp-atlassian`) **is not currently used** — considered for future integrations with other tools.

#### JiraStatus Enum

```python
# app/utils/jira_status.py
from enum import StrEnum

class JiraStatus(StrEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
```

#### Polling: Direct REST API

Polling uses **direct REST API** for better reliability:

```python
# app/mcp/polling.py
import base64
import urllib.parse
import urllib.request

async def search_ready_for_dev_tickets():
    auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    jql = urllib.parse.quote(f"status = '{JiraStatus.TO_DO}' ORDER BY created ASC")
    url = f"{JIRA_URL}/rest/api/3/search/jql?jql={jql}&maxResults=10"
    # Uses urllib.request directly for polling
```

#### Jira Tools Available to Agents

| MCP Tool | Use in Pipeline |
|---|---|
| `jira_search_issues` | Search tickets by JQL |
| `jira_get_issue` | Read full ticket details |
| `jira_update_issue` | Change status (In Progress, Done, Blocked) |
| `jira_add_comment` | Comment progress, errors, PR link |
| `jira_get_comments` | Read comments/additional context |
| `jira_add_issues_to_sprint` | Sprint organization |

**Note:** Jira tools are not implemented via MCP. Future integration via Jira webhook.

### MCP Servers (Future)

#### GitHub MCP

To create branches and PRs, the official GitHub MCP server will be used:

```python
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

github_mcp = MCPClient(
    lambda: streamablehttp_client(
        url="https://api.githubcopilot.com/mcp/",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    ),
    prefix="github",
)
```

### Trigger: Polling (MVP) + Webhook (Future)

**MVP (current):** Polling searches for "To Do" tickets every N minutes using direct REST API.

**Future:** Jira webhook → API Gateway → FastAPI for real-time detection.

### Ticket Lifecycle

| Event | Action (via MCP tools) |
|---|---|
| Ticket detected (polling) | Direct API → `launch_agent_pipeline(ticket_id)` |
| Pipeline started | `jira_update_issue` → "In Progress" + `jira_add_comment` |
| PR created | `jira_add_comment` → PR link |
| Tests failed | `jira_add_comment` + `jira_update_issue` → "Blocked" |
| Review approved | `jira_update_issue` → "Done" |

---

## 5. Development Agents with Strands SDK (✅ Completed)

### 5.1 MiniMax M2.7 Connection

MiniMax exposes an OpenAI-compatible endpoint. Strands supports `OpenAIModel` natively.

```python
from strands.models.openai import OpenAIModel

minimax = OpenAIModel(
    client_args={
        "api_key": MINIMAX_API_KEY,
        "base_url": MINIMAX_API_URL,  # configurable: api.minimax.io or openrouter
    },
    model_id="MiniMax-M2.7",
)
```

### 5.2 Tools: strands_tools + MCP

Agents use a combination of **native strands_tools** (file/code operations) and **MCP clients** (only GitHub in the future).

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write, editor, shell, python_repl, current_time
from mcp import stdio_client, StdioServerParameters

# --- MCP Clients (future) ---
github_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        )
    ),
    prefix="github",
)

# --- Tools by agent type ---
ORCHESTRATOR_TOOLS = [github_mcp]                    # MCP: creates PR (future)
DEV_TOOLS = [file_read, file_write, editor, shell]    # strands_tools: operates on code
QA_TOOLS = [file_read, file_write, shell, python_repl] # strands_tools: writes and runs tests
```

#### Tools Map

| Tool | Source | Agents Using It |
|---|---|---|
| `file_read` | strands_tools | Backend, Frontend, QA |
| `file_write` | strands_tools | Backend, Frontend, QA |
| `editor` | strands_tools | Backend, Frontend (edit existing code) |
| `shell` | strands_tools | QA (run tests), Backend (migrations) |
| `python_repl` | strands_tools | QA (execute tests inline) |
| `current_time` | strands_tools | Orchestrator (timestamps in logs) |
| `github_create_branch` | MCP (github, future) | Orchestrator |
| `github_create_pull_request` | MCP (github, future) | Orchestrator |

### 5.3 Agent Definitions

Each agent has a clear role, limited system prompt, and specific tools. MCP clients are passed directly — Strands handles their lifecycle.

#### Architect Agent (Orchestrator)

Receives Jira ticket (via direct API), analyzes requirements, decomposes into subtasks, and coordinates other agents (passed as tools).

```python
from strands import Agent

backend_agent = create_backend_agent(minimax)
frontend_agent = create_frontend_agent(minimax)
qa_agent = create_qa_agent(minimax)

orchestrator = Agent(
    model=minimax,
    system_prompt="""You are a software architect orchestrator.
You receive Jira ticket IDs and orchestrate their implementation.

Workflow:
1. Use Jira API to read ticket details (jira_get_issue equivalent)
2. Use Jira API to set status to "In Progress" (jira_update_issue equivalent)
3. Use Jira API to log that work has started (jira_add_comment equivalent)
4. Analyze requirements and determine which agents to call
5. Call backend_agent and/or frontend_agent with specific tasks
6. Call qa_agent to validate the generated code
7. Use shell to run: git checkout -b agent/<ticket-id> && git add . && git commit
8. Use github_create_pull_request to create the PR
9. Use Jira API to post the PR link (jira_add_comment equivalent)
10. If any agent fails twice, use Jira API to set "Blocked" and log error

Available agents:
- backend_agent: Server-side code, APIs, database models, business logic
- frontend_agent: UI components, pages, client-side logic
- qa_agent: Unit tests, integration tests, runs test suites
""",
    tools=[
        *ORCHESTRATOR_TOOLS,    # github_mcp (future)
        current_time,
        shell,                  # for git operations
        backend_agent,
        frontend_agent,
        qa_agent,
    ],
)
```

#### Backend Developer Agent

```python
def create_backend_agent(model) -> Agent:
    return Agent(
        name="backend_agent",
        model=model,
        system_prompt="""You are a senior Python backend developer.
You work with FastAPI, Pydantic, SQLAlchemy, and follow clean architecture.

You have tools to read, write, and edit files directly. Use them — do NOT output
code blocks. Instead, use file_write to create files and editor to modify existing ones.

Conventions:
- Type hints on all functions
- Pydantic models for request/response validation
- Async endpoints with FastAPI
- Repository pattern for database access
""",
        tools=DEV_TOOLS,
    )
```

#### Frontend Developer Agent

```python
def create_frontend_agent(model) -> Agent:
    return Agent(
        name="frontend_agent",
        model=model,
        system_prompt="""You are a senior React/TypeScript frontend developer.
You work with React, Vite, TypeScript, and follow component-based architecture.

You have tools to read, write, and edit files directly. Use them — do NOT output
code blocks. Instead, use file_write to create files and editor to modify existing ones.

Conventions:
- Functional components with TypeScript interfaces for props
- Custom hooks for API calls and state management
- CSS modules or Tailwind for styling
""",
        tools=DEV_TOOLS,
    )
```

#### QA Agent

```python
def create_qa_agent(model) -> Agent:
    return Agent(
        name="qa_agent",
        model=model,
        system_prompt="""You are a QA engineer specialized in automated testing.
You write tests for Python (pytest) and React (vitest/testing-library).

Workflow:
1. Use file_read to read the code generated by backend/frontend agents
2. Use file_write to create test files
3. Use shell to run: pytest tests/ --tb=short (backend) or npm run test (frontend)
4. If tests fail, return failure details so the architect can request fixes
5. If tests pass, return a summary of coverage

You MUST run the tests, not just write them.
""",
        tools=QA_TOOLS,
    )
```

### 5.4 Alternative: Graph Builder for Sequential Flows

For tickets where the flow is always linear (Backend → Frontend → QA), you can use `GraphBuilder`:

```python
from strands import Agent, GraphBuilder

builder = GraphBuilder()
builder.add_node(backend_agent, "backend")
builder.add_node(frontend_agent, "frontend")
builder.add_node(qa_agent, "qa")
builder.add_edge("backend", "frontend")
builder.add_edge("frontend", "qa")
builder.set_entry_point("backend")

pipeline = builder.build()
result = pipeline(f"Implement Jira ticket: {ticket_context}")
```

### 5.5 Complete Pipeline

```python
import uuid

async def launch_agent_pipeline(ticket_id: str) -> str:
    """Launches the agent pipeline for a Jira ticket."""
    session_id = str(uuid.uuid4())

    # Save session to DB
    await save_session(session_id, ticket_id, status="started")

    # Emit event to dashboard
    await emit_event(session_id, "pipeline_started", {"ticket_id": ticket_id})

    try:
        # The orchestrator does EVERYTHING via tools (MCP + strands_tools):
        # - Reads ticket from Jira (jira_get_issue)
        # - Transitions it to "In Progress" (jira_update_issue)
        # - Delegates to dev agents (backend_agent, frontend_agent, qa_agent)
        # - Creates branch and PR (shell + github_create_pull_request)
        # - Comments on Jira with PR link (jira_add_comment)
        result = orchestrator(
            f"Implement Jira ticket {ticket_id}. "
            f"Read the ticket, implement the solution, run tests, "
            f"create a PR, and update Jira with the results. "
            f"Working directory: /app/workspaces/{ticket_id.lower()}"
        )

        await save_session(session_id, ticket_id, status="completed", result=str(result))

    except Exception as e:
        await save_session(session_id, ticket_id, status="error", error=str(e))
        await emit_event(session_id, "pipeline_error", {"error": str(e)})

    return session_id
```

---

## 6. Security and Guardrails

### Security
- API keys in `.env` (git-ignored). In production, inject as cloud provider secrets
- Agents execute code in **isolated directories** (`/app/workspaces/<ticket-id>/`)
- Branch protection rules prevent merge without review
- MCP servers run as backend subprocesses, not exposed externally

### Anti-Loop Guardrails and Billing Control

> **CRITICAL for PoC and production.** Agents can enter infinite loops that consume tokens non-stop. These guardrails are mandatory.

#### Per-Agent Limits

```python
from strands import Agent

agent = Agent(
    model=minimax,
    system_prompt="...",
    tools=[...],
)
```

#### Limit Configuration

| Guardrail | Default Value | Description |
|---|---|---|
| **Agent timeout** | 5 min | Agent is cancelled if exceeded |
| **Max iterations (tool calls)** | 20 | Max tool calls per agent invocation |
| **Max orchestrator iterations** | 50 | Orchestrator has more margin because it coordinates |
| **Token budget per session** | 100k tokens | Tracked and cut if exceeded |
| **Max files per agent** | 15 | Prevents an agent from creating infinite files |
| **Max file size** | 500 lines | If an agent generates more, it's cut and reports error |

#### Token Tracker Implementation

```python
import time
from dataclasses import dataclass, field

@dataclass
class SessionBudget:
    max_tokens: int = 100_000
    max_duration_seconds: int = 600
    max_tool_calls_per_agent: int = 20

    tokens_used: int = 0
    start_time: float = field(default_factory=time.time)
    tool_calls: dict[str, int] = field(default_factory=dict)

    def track_tokens(self, agent_id: str, tokens: int):
        self.tokens_used += tokens
        if self.tokens_used > self.max_tokens:
            raise BudgetExceededError(
                f"Session token budget exceeded: {self.tokens_used}/{self.max_tokens}"
            )

    def track_tool_call(self, agent_id: str):
        self.tool_calls[agent_id] = self.tool_calls.get(agent_id, 0) + 1
        if self.tool_calls[agent_id] > self.max_tool_calls_per_agent:
            raise BudgetExceededError(
                f"Agent {agent_id} exceeded max tool calls: "
                f"{self.tool_calls[agent_id]}/{self.max_tool_calls_per_agent}"
            )

    def check_timeout(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.max_duration_seconds:
            raise BudgetExceededError(
                f"Session timeout: {elapsed:.0f}s / {self.max_duration_seconds}s"
            )

class BudgetExceededError(Exception):
    pass
```

#### What Happens When a Limit is Exceeded

1. The agent stops immediately
2. Partial state is saved to DB
3. `budget_exceeded` event is emitted to dashboard
4. Comment posted to Jira: "Agent pipeline paused — budget exceeded. Manual intervention required."
5. Ticket is transitioned to "Blocked"

### Error Handling
- Retry with exponential backoff on MiniMax API calls
- Circuit breaker if MiniMax is down (notifies and pauses)
- Per-agent timeout (configurable, default 5 min)
- If an agent fails 2 times, the orchestrator marks the ticket as "Blocked" in Jira

### Costs
- **MiniMax M2.7**: check current pricing at https://platform.minimax.io/subscribe/token-plan
- **Infra**: PostgreSQL + Docker containers — fixed and predictable cost
- **No serverless services** that scale unexpectedly
- Token budget guardrails are the main protection against surprise billing

### Observability
- Logs in stdout (structured JSON) + PostgreSQL (`agent_events` table) + Socket.IO dashboard
- In production, add log collector (Loki, ELK, or cloud provider's native solution)

---

## 7. Monitoring Dashboard (MVP)

### 7.1 Architecture

```
PostgreSQL → Socket.IO (FastAPI) → React Dashboard
                                               ↓
                                          Canvas 2D (SVG)
                                          AgentFigures
                                          LogPanel
                                          MetricsPanel
```

### 7.2 Real-Time Communication (Socket.IO)

```python
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

async def emit_event(session_id: str, event_type: str, payload: dict):
    """Emits event to all clients connected to the session room."""
    await sio.emit("agent_event", {
        "type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }, room=session_id)

@sio.event
async def join_session(sid, data):
    """Client joins a session room to receive events."""
    sio.enter_room(sid, data["session_id"])
    state = await get_session_state(data["session_id"])
    await sio.emit("state_sync", state, to=sid)
```

#### Message Format

```json
{
  "type": "agent_state_change",
  "session_id": "abc-123",
  "timestamp": "2026-03-29T10:30:00Z",
  "payload": {
    "agent_id": "backend_agent",
    "previous_state": "idle",
    "new_state": "working",
    "task": "Creating user model and API endpoints",
    "progress": 0.3
  }
}
```

Event types: `agent_state_change`, `agent_log`, `task_assigned`, `task_completed`, `error`, `pipeline_started`, `pipeline_completed`, `pr_created`.

### 7.3 2D Figure System (SVG Sprites)

Each agent is represented as a simple SVG character with CSS animations per state.

#### Visual States

| State | Visual | CSS Animation |
|---|---|---|
| `idle` | Neutral character, base color | `animate-bob` (soft vertical float 2px, 2s) |
| `thinking` | Thought bubble with "..." | `animate-pulse` (pulsing opacity, 1s) |
| `working` | Activity particles, active tool | `animate-work` (hand movement, 0.5s) |
| `waiting` | Hourglass or "?" above head | `animate-wait` (slow opacity, 3s) |
| `success` | Green check, happy expression | `animate-bounce` (bounce, 0.5s) |
| `error` | Red "!", worried expression | `animate-shake` (horizontal vibration, 0.3s) |

#### Design by Role

| Agent | Primary Color | Distinctive Element |
|---|---|---|
| **Architect** | Navy blue `#1E3A5F` | Hat/helmet + blueprint |
| **Backend** | Emerald green `#0D7377` | Terminal/prompt + headphones |
| **Frontend** | Coral `#FF6B6B` | Color palette + round glasses |
| **QA** | Orange `#F0932B` | Giant magnifying glass + lab coat |

#### React Component

```tsx
interface AgentFigureProps {
  agent: {
    id: string;
    name: string;
    role: "architect" | "backend" | "frontend" | "qa";
    state: "idle" | "thinking" | "working" | "waiting" | "success" | "error";
    task?: string;
    progress?: number;
  };
}

const ANIMATION_CLASS: Record<string, string> = {
  idle: "animate-bob",
  thinking: "animate-pulse",
  working: "animate-work",
  waiting: "animate-wait",
  success: "animate-bounce",
  error: "animate-shake",
};

const AgentFigure: React.FC<AgentFigureProps> = ({ agent }) => (
  <g className={`agent agent-${agent.role} ${ANIMATION_CLASS[agent.state]}`}>
    <AgentSprite role={agent.role} state={agent.state} />

    {agent.state === "thinking" && <ThoughtBubble />}
    {agent.state === "working" && agent.progress != null && (
      <ProgressRing progress={agent.progress} />
    )}
    {agent.state === "error" && <ErrorIndicator />}

    <text className="agent-name" textAnchor="middle" y={120}>
      {agent.name}
    </text>
    {agent.task && (
      <text className="agent-task" textAnchor="middle" y={136} fontSize={10}>
        {agent.task}
      </text>
    )}
  </g>
);
```

#### Connections Between Agents

```tsx
const AgentConnection: React.FC<{ from: Point; to: Point; active: boolean }> = ({
  from, to, active,
}) => (
  <line
    x1={from.x} y1={from.y}
    x2={to.x} y2={to.y}
    stroke={active ? "#4A90D9" : "#ccc"}
    strokeWidth={active ? 2 : 1}
    strokeDasharray={active ? "8 4" : "none"}
    className={active ? "animate-dash" : ""}
  />
);
```

### 7.4 Dashboard Layout

```
┌──────────────┬──────────────────────────────┬──────────────┐
│              │                              │              │
│  Task List   │     Central Canvas (60%)     │   Log Panel  │
│   (20%)      │                              │    (20%)     │
│              │   ┌─────┐     ┌─────┐       │              │
│  PROJ-123    │   │Arch │────→│Back │       │  [backend]   │
│  ├─ Backend  │   └──┬──┘     └──┬──┘       │  Creating    │
│  ├─ Frontend │      │           │           │  user model  │
│  └─ QA       │      │       ┌───┴──┐       │              │
│              │      └──────→│Front │       │  [qa]        │
│  Status:     │              └───┬──┘       │  Waiting...  │
│  In Progress │                  │           │              │
│              │              ┌───┴──┐       │              │
│              │              │  QA  │       │              │
│              │              └──────┘       │              │
│              │                              │              │
└──────────────┴──────────────────────────────┴──────────────┘
│                    Metrics Bar                              │
│  Tokens: 12.4k  │  Time: 2m 30s  │  Files: 8  │  Tests: ✓ │
└─────────────────────────────────────────────────────────────┘
```

### 7.5 Dashboard Components

| Component | Responsibility |
|---|---|
| `AgentCanvas` | Central SVG canvas, renders figures and connections |
| `AgentFigure` | Individual sprite with state and animation |
| `TaskPanel` | Ticket task list, state of each |
| `LogPanel` | Real-time logs, filterable by agent |
| `MetricsBar` | Tokens used, time, files generated, test status |
| `ConnectionStatus` | Socket.IO connection status with auto-reconnect |

---

## 8. Human-in-the-Loop: Review and CI/CD

Generated code by agents **never goes directly to production**. The approval flow:

```
Agents generate code
       ↓
Git branch: agent/proj-123
       ↓
Automatic Pull Request (GitHub/CodeCommit)
       ↓
CI/CD Pipeline activates:
  ├── Linting (ruff, eslint)
  ├── Unit tests (pytest, vitest)
  ├── Integration tests
  ├── Security scan (bandit, npm audit)
  └── Build check
       ↓
  ┌─────────────────────────┐
  │  HUMAN REVIEW REQUIRED  │
  │                         │
  │  - PR code review       │
  │  - Verify quality       │
  │  - Approve or reject    │
  └─────────────────────────┘
       ↓ (if approved)
  Merge → Deploy to staging → Deploy to prod
```

### Branch Protection Configuration

```yaml
# GitHub branch protection (configure via UI or API)
branch_protection:
  required_reviews: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: true
  required_status_checks:
    - lint
    - test-backend
    - test-frontend
    - security-scan
```

### Generic CI/CD (CodeBuild/GitHub Actions)

```yaml
# buildspec.yml for CodeBuild / .github/workflows/ci.yml
version: 0.2
phases:
  install:
    commands:
      - pip install -r requirements.txt
      - npm ci
  build:
    commands:
      - ruff check .
      - pytest tests/ --tb=short
      - cd frontend && npm run lint && npm run test
  post_build:
    commands:
      - echo "All checks passed — awaiting human review"
```

---

## 9. Operational Runbook

### 9.1 Common Operations

#### Start the system (local)

```bash
# 1. Verify Docker is running
docker --version

# 2. Start all services
docker compose up -d

# 3. Check service status
docker compose ps

# 4. View real-time logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 5. Verify Jira API connection
docker compose exec backend curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/myself" | head -c 200
```

#### Stop the system

```bash
# Stop all services (preserves data)
docker compose stop

# Stop and remove volumes (DELETES DATA)
docker compose down -v
```

#### Restart a specific service

```bash
docker compose restart backend
docker compose restart frontend
docker compose restart db
```

---

### 9.2 Health Verification

#### Healthchecks

```bash
# Backend API
curl -f http://localhost:8000/health

# Frontend
curl -f http://localhost:5173

# PostgreSQL
docker compose exec db pg_isready -U agent -d multi_agent

# WebSocket (Socket.IO)
curl -f http://localhost:8000/socket.io/?EIO=4&transport=polling
```

#### Pipeline Health Checklist

| Component | Verification | Command |
|---|---|---|
| **PostgreSQL** | Active connection | `docker compose exec db psql -U agent -d multi_agent -c "SELECT 1"` |
| **MiniMax API** | API responds | `curl -s -o /dev/null -w "%{http_code}" https://api.minimax.io/v1/models` |
| **Jira API** | API responds | `curl -s -o /dev/null -w "%{http_code}" https://your-domain.atlassian.net/rest/api/3/myself` |
| **GitHub MCP** | Valid token | `gh auth status` |
| **strands_tools** | Tools load | `python -c "from strands_tools import file_read, file_write; print('OK')"` |

---

### 9.3 Incident Handling

#### Failed Pipeline — Blocked Ticket

**Symptom**: Jira ticket is in "Blocked" status or PR was not created.

**Diagnosis**:
```bash
# 1. Check backend logs
docker compose logs backend --tail=100 | grep -i error

# 2. Verify workspace exists
ls -la workspaces/

# 3. Check session state in DB
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT id, ticket_id, status, error FROM agent_sessions ORDER BY created_at DESC LIMIT 5;"
```

**Resolution**:
```bash
# 1. Clean ticket workspace
rm -rf workspaces/<ticket-id>/

# 2. Reset state in Jira (manual or via UI)

# 3. Re-launch pipeline manually
curl -X POST http://localhost:8000/trigger/<ticket-id>
```

#### Jira/GitHub Authentication Error

**Symptom**: `AuthenticationError` in logs.

**Diagnosis**:
```bash
# Verify environment variables
docker compose exec backend env | grep -E "(JIRA|GITHUB)"

# Test Jira token
docker compose exec backend curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_URL/rest/api/2/myself" | head -c 200

# Test GitHub token
gh auth status
```

**Resolution**:
```bash
# Update secrets in .env
# Restart backend
docker compose restart backend
```

#### Budget exceeded (tokens/iterations)

**Symptom**: `BudgetExceededError` in logs, ticket in "Blocked".

**Diagnosis**:
```bash
# Check token consumption
docker compose logs backend | grep -i "budget\|tokens"

# Check last budget event
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT * FROM agent_events WHERE event_type = 'budget_exceeded' ORDER BY created_at DESC LIMIT 3;"
```

**Resolution**:
```bash
# Increase limits in config (temporarily)
# Or clear session and retry
docker compose exec db psql -U agent -d multi_agent -c \
  "DELETE FROM agent_events WHERE session_id = '<session-id>';"
```

#### MiniMax API Not Responding

**Symptom**: `ConnectionError` or timeout on LLM calls.

**Diagnosis**:
```bash
# Test connectivity
curl -v https://api.minimax.io/v1/models \
  -H "Authorization: Bearer $MINIMAX_API_KEY" 2>&1 | head -20

# Check rate limits
curl -s https://api.minimax.io/v1/usage \
  -H "Authorization: Bearer $MINIMAX_API_KEY"
```

**Resolution**:
```bash
# Wait and retry (automatic backoff if implemented)
# If problem persists, check MiniMax status
# Alternative: use OpenRouter as fallback
```

#### Model reaches 70% usage (dynamic switch)

**Symptom**: ~70% of current model's token quota reached.

**Configured models**:
- **Primary**: `MiniMax-M2.7` via api.minimax.io
- **Fallback**: `MiniMax-M2.7` via OpenRouter

**Resolution (manual switch to fallback)**:
```bash
# Change MINIMAX_API_URL in .env to OpenRouter
sed -i 's|MINIMAX_API_URL=.*|MINIMAX_API_URL=https://openrouter.ai/api/v1|' .env
docker compose restart backend
```

---

### 9.4 Recovery Procedures

#### Disaster Recovery — PostgreSQL Loss

```bash
# 1. Verify volume persists
docker compose inspect db | grep -A5 "Mounts"

# 2. If there is a backup, restore
docker compose exec db psql -U agent -d multi_agent < backup.sql

# 3. If no backup and there are workspaces:
#    Agents can regenerate code from the PR
#    Only events/historic are lost
```

#### Corrupt Workspace Recovery

```bash
# 1. Identify problematic workspaces
ls -la workspaces/

# 2. Regenerate from PR
#    - The PR contains all generated code

# 3. Clean workspace
rm -rf workspaces/<ticket-id>/
```

---

### 9.5 Debugging Commands

```bash
# View all events from a session
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT agent_id, event_type, created_at FROM agent_events \
   WHERE session_id = '<session-id>' ORDER BY created_at;"

# View logs from a specific agent
docker compose logs -f backend 2>&1 | grep "backend_agent"

# View resource consumption
docker stats

# View environment variables loaded in backend
docker compose exec backend env | sort

# Access shell in container
docker compose exec backend /bin/bash

# Verify dependency versions
docker compose exec backend pip list | grep -E "(strands|fastapi|socketio)"

# Test MCP manually
docker compose exec backend python -c "
from mcp import stdio_client, StdioServerParameters
print('MCP client imported OK')
"
```

---

### 9.6 Contacts and Escalation

| Level | Responsible | When to Escalate |
|---|---|---|
| **L1** | DevOps on-call | Failed pipeline, connection errors |
| **L2** | Backend Lead | Agent bugs, memory leaks, performance |
| **L3** | Architect | Agent design, flow changes, major incidents |

---

## 10. Future / Desired

> The following functionalities **are not part of the MVP** but are planned for future iterations.

### 10.1 Jira Webhook Integration

Replace polling with **Jira webhooks** for real-time ticket detection:

- Jira webhook → API Gateway (Cloudflare/Railway) → FastAPI endpoint
- Eliminates polling interval delay
- More efficient in API calls
- Requires: publicly exposed endpoint or tunnel (ngrok/cloudflared)

### 10.2 Production Remediation Agents

Use agents to **diagnose and automatically resolve production errors**:

- CloudWatch Alarm → EventBridge → Lambda → Strands Orchestrator
- Diagnostic Agent: analyzes logs, metrics, error traces
- Remediation Agent: executes corrective actions (scale instance, rollback, restart service)
- Validation Agent: verifies fix worked
- Requires: IAM roles with execution permissions, strict guardrails, predefined runbooks

### 10.2 DevOps Agent

Agent that generates and maintains IaC (CDK/CloudFormation), Dockerfiles, and CI/CD pipelines.

### 10.3 Documentation Agent

Generates and maintains README, API docs, and contribution guides from generated code.

### 10.4 Review Learning

Store human code review feedback so agents improve over time (fine-tuning or RAG over PR comments).

### 10.5 Advanced Dashboard

- Sprite sheets with pixel art and advanced animations
- Light/dark themes
- Configurable agent skins
- Historical metrics and analytics
- **Reference for pixel art agent visualization**: [Pixel Agents](https://github.com/pablodelucca/pixel-agents) — VS Code extension with pixel art office, Canvas 2D game loop, BFS pathfinding, character state machine, and modular asset system (sprites, furniture, floors). 5.7k stars. Agent-agnostic and platform-agnostic architecture designed to extend beyond Claude Code.

### 10.6 AgentCore with Full AWS (Alternative Architecture)

**Future alternative for teams already invested in AWS.**

| Criteria | Strands SDK (MVP) | Bedrock AgentCore (Future) |
|---|---|---|
| External LLM (MiniMax) | **Yes** — `OpenAIModel` provider | No — Bedrock models only |
| Flow control | Total, it's your Python code | Managed, less flexibility |
| Infra cost | Only ECS + LLM API | AgentCore Runtime + LLM |
| Multi-agent patterns | Agents-as-tools, GraphBuilder, Swarm | Limited to Bedrock agents |
| Learning curve | Moderate, good docs | Low but less flexible |
| Demo-friendliness | **High** — you can show the code | More "black box" |
| Vendor lock-in | **Low** — cloud-agnostic | High — AWS only |

**When to consider migrating to AgentCore:**
- Team already has deep AWS experience
- Native Bedrock integration needed (Claude, etc.)
- Management simplicity prioritized over control
- AgentCore Runtime cost is acceptable

**Note:** The current architecture (Strands + Docker + PostgreSQL) is designed to be cloud-agnostic. If migrating to Bedrock in the future, Strands supports both without significant architectural changes.

#### DynamoDB as PostgreSQL Alternative (AWS)

For AWS deployment, PostgreSQL can be replaced with DynamoDB:

| Table | PK | SK | Use |
|---|---|---|---|
| `AgentSessions` | `session_id` | `#metadata` | Pipeline state |
| `AgentEvents` | `session_id` | `timestamp#event_id` | Dashboard events |
| GSI: `TicketIndex` | `ticket_id` | `created_at` | Search by ticket |

The data access layer is abstracted with a **repository pattern** so the PostgreSQL → DynamoDB switch is transparent.

```
DynamoDB Streams → Lambda → Socket.IO (FastAPI) → React Dashboard
```

---

## 11. Reference Resources

### Strands SDK
- [Strands Agents SDK — Docs](https://strandsagents.com)
- [Strands — Multi-Agent Patterns (agents-as-tools)](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/multi-agent/agents-as-tools.mdx)
- [Strands — GraphBuilder](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/multi-agent/graph.mdx)
- [Strands — MCP Integration](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/tools/mcp-tools.mdx)
- [Strands Tools (file_read, file_write, editor, shell, etc.)](https://github.com/strands-agents/tools)
- [Strands — Custom Model Providers](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/model-providers/custom_model_provider.mdx)

### MCP Servers (Future)
- [GitHub MCP Server (@modelcontextprotocol/server-github)](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

### LLM
- [MiniMax API — OpenAI Compatible Endpoint](https://platform.minimax.io/docs/api-reference/text-openai-api)
- [MiniMax Token Plans](https://platform.minimax.io/subscribe/token-plan)
- [OpenRouter — MiniMax M2.7](https://openrouter.ai/minimax/minimax-m2.7)

### Architecture Reference
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Pixel Agents — Visual runtime for AI agents with pixel art](https://github.com/pablodelucca/pixel-agents)
