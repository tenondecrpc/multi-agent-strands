# Sistema Multi-Agente para Desarrollo de Software via Jira

## 1. Visión General

Sistema multi-agente que se activa automáticamente cuando se crea o actualiza un ticket en Jira. Agentes especializados de desarrollo de software (Arquitecto, Backend, Frontend, QA) analizan el ticket, generan código, ejecutan tests y crean un Pull Request. **Un humano siempre revisa y aprueba antes de merge a producción.**

### Flujo Principal

```
Jira Ticket (el orquestador lo lee via MCP)
       ↓
Strands SDK Orchestrator Agent
  ├── MCP: Jira (lee ticket, actualiza estado, comenta)
  ├── MCP: GitHub (crea branch, PR)
  ↓ descompone el ticket
  ┌────┼────┬────────┐
  ↓    ↓    ↓        ↓
Arch  Back  Front    QA
Agent Agent Agent  Agent
  │    (strands_tools: file_read, file_write, editor, shell)
  └────┼────┴────────┘
       ↓ código generado
  Git Branch + Pull Request (via MCP GitHub)
       ↓
  CI/CD Pipeline
       ↓ tests automáticos
  Human Review & Approve
       ↓
  Runbook: Validación y Documentación
       ↓
  Merge → Deploy a Prod
```

### Principios

- **Human-in-the-loop**: El código generado NUNCA va directo a producción. Siempre pasa por PR + review humano.
- **Modelo económico**: MiniMax M2.7 como LLM principal via API OpenAI-compatible.
- **Cloud-agnostic**: Docker + PostgreSQL en local y producción. Sin dependencia de servicios cloud específicos.
- **MCP-first**: Jira y GitHub se integran via MCP servers, no APIs directas.
- **Guardrails de billing**: Timeouts, límites de iteraciones y token budgets por agente para evitar loops infinitos.
- **Strands tools**: Los agentes usan `strands_tools` (file_read, file_write, editor, shell) para operar sobre el código.
- **Observable**: Dashboard Canvas 2D en tiempo real via Socket.IO.

---

## 2. Stack Tecnológico (MVP)

### Frontend
- **React + Vite + TypeScript**
- **Socket.IO client** para eventos en tiempo real
- **Canvas 2D (SVG + CSS animations)** para dashboard de agentes

### Backend
- **FastAPI (Python 3.12+)**
- **Strands Agents SDK** — orquestación multi-agente
- **strands_tools** — tools nativos: `file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`
- **MCP clients** — Jira (`mcp-atlassian`) y GitHub (`github-mcp-server`) como tools de los agentes
- **Pydantic** — validación de datos
- **python-socketio** — servidor Socket.IO
- **SQLAlchemy + asyncpg** — ORM para PostgreSQL

### LLM
- **MiniMax M2.7** via API OpenAI-compatible, dos proveedores interchangeably:
  - `https://api.minimax.io/v1` (MiniMax official)
  - `https://openrouter.ai/minimax/minimax-m2.7` (OpenRouter)
- Integración con Strands via `OpenAIModel` provider (sin custom provider necesario)

### Base de Datos
- **PostgreSQL 16** — tanto en local (Docker) como en producción (cualquier proveedor: RDS, Cloud SQL, self-hosted, etc.)

### Entorno (Docker Compose)

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌──────────┐  ┌──────────────────────────────────────┐ │
│  │PostgreSQL│  │ FastAPI + Strands SDK                 │ │
│  │  :5432   │  │   ├── MCP: mcp-atlassian (Jira)      │ │
│  └──────────┘  │   ├── MCP: github-mcp-server          │ │
│       ↑        │   ├── strands_tools (file/shell/edit) │ │
│       └────────│   └── Socket.IO server                │ │
│                └──────────┬───────────────────────────┘ │
│                           ↓                              │
│                    MiniMax API (externo)                  │
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
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    depends_on:
      - db
    volumes:
      - ./workspaces:/app/workspaces  # directorio donde los agentes escriben código

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_SOCKET_URL: http://localhost:8000

volumes:
  pgdata:
```

### Producción

El mismo `docker-compose.yml` funciona en producción. El stack es cloud-agnostic — puede desplegarse en cualquier proveedor que soporte Docker:

| Opción | Cómo |
|---|---|
| **VPS / bare metal** | `docker compose up -d` directamente |
| **AWS** | ECS Fargate + RDS PostgreSQL |
| **GCP** | Cloud Run + Cloud SQL |
| **Azure** | Container Apps + Azure Database for PostgreSQL |
| **Railway / Render** | Deploy directo desde Docker Compose |

Para producción, agregar:
- **Reverse proxy** (Nginx/Caddy) con TLS
- **Secrets management** (env vars inyectadas por el proveedor, no en `.env`)
- **Persistent volume** para `/app/workspaces`
- **PostgreSQL managed** (o el mismo container con volume persistente)

---

## 3. Integración con Jira via MCP

### MCP Server: mcp-atlassian

En lugar de integrar Jira via API directa o webhooks, los agentes acceden a Jira como **MCP tools** usando [`mcp-atlassian`](https://github.com/sooperset/mcp-atlassian) (72 tools, soporta Jira Cloud y Server/Data Center).

```python
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

# MCP client para Jira (stdio transport — corre como subproceso)
jira_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["mcp-atlassian"],
            env={
                "JIRA_URL": JIRA_URL,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
                "JIRA_EMAIL": JIRA_EMAIL,
            },
        )
    ),
    prefix="jira",  # tools se exponen como jira_search_issues, jira_get_issue, etc.
)
```

#### Tools de Jira disponibles para los agentes

| MCP Tool | Uso en el pipeline |
|---|---|
| `jira_search_issues` | Buscar tickets "Ready for Dev" (JQL) |
| `jira_get_issue` | Leer detalle completo del ticket |
| `jira_update_issue` | Cambiar estado (In Progress, Done, Blocked) |
| `jira_add_comment` | Comentar progreso, errores, link al PR |
| `jira_get_comments` | Leer comentarios/contexto adicional del ticket |
| `jira_add_issues_to_sprint` | Organización de sprint |

### MCP Server: GitHub

Para crear branches y PRs, se usa el MCP server oficial de GitHub:

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

### Trigger: Polling o Webhook

Para pruebas locales, el orquestador hace **polling** a Jira via MCP buscando tickets en estado "Ready for Dev":

```python
# Endpoint manual para trigger local
@app.post("/trigger/{ticket_id}")
async def trigger_pipeline(ticket_id: str):
    """Trigger manual: lanza pipeline para un ticket específico."""
    session_id = await launch_agent_pipeline(ticket_id)
    return {"session_id": session_id}

# Polling automático (opcional, para demo)
async def poll_jira_for_ready_tickets():
    """Busca tickets 'Ready for Dev' cada N minutos via MCP."""
    # El orquestador usa jira_search_issues internamente
    orchestrator(
        "Search Jira for issues with status 'Ready for Dev' "
        "in project PROJ. For each one, start the development pipeline."
    )
```

Para producción se puede agregar un **Jira webhook → API Gateway → FastAPI** que invoque el mismo pipeline, pero el agente sigue usando MCP para leer/actualizar el ticket.

### Ciclo de vida del ticket

| Evento | Acción (via MCP tools) |
|---|---|
| Ticket detectado | `jira_get_issue` → lee contexto completo |
| Pipeline iniciado | `jira_update_issue` → "In Progress" + `jira_add_comment` |
| PR creado | `jira_add_comment` → link al PR |
| Tests pasaron | `jira_add_comment` → resultados |
| Tests fallaron | `jira_add_comment` + `jira_update_issue` → "Blocked" |
| Review aprobado | `jira_update_issue` → "Done" |

---

## 4. Agentes de Desarrollo con Strands SDK

### 4.1 Conexión con MiniMax M2.7

MiniMax expone un endpoint OpenAI-compatible. Strands soporta `OpenAIModel` nativamente.

```python
from strands.models.openai import OpenAIModel

minimax = OpenAIModel(
    client_args={
        "api_key": MINIMAX_API_KEY,
        "base_url": MINIMAX_API_URL,  # configurable: api.minimax.io o openrouter
    },
    model_id="MiniMax-M2.7",
)
```

### 4.2 Tools: strands_tools + MCP

Los agentes usan una combinación de **strands_tools nativos** (operaciones sobre archivos/código) y **MCP clients** (Jira, GitHub).

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write, editor, shell, python_repl, current_time
from mcp import stdio_client, StdioServerParameters

# --- MCP Clients ---
jira_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["mcp-atlassian"],
            env={
                "JIRA_URL": JIRA_URL,
                "JIRA_API_TOKEN": JIRA_API_TOKEN,
                "JIRA_EMAIL": JIRA_EMAIL,
            },
        )
    ),
    prefix="jira",
)

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

# --- Tools por tipo de agente ---
ORCHESTRATOR_TOOLS = [jira_mcp, github_mcp]          # MCP: lee/actualiza Jira, crea PR
DEV_TOOLS = [file_read, file_write, editor, shell]    # strands_tools: opera sobre código
QA_TOOLS = [file_read, file_write, shell, python_repl] # strands_tools: escribe y corre tests
```

#### Mapa de tools

| Tool | Source | Agentes que lo usan |
|---|---|---|
| `file_read` | strands_tools | Backend, Frontend, QA |
| `file_write` | strands_tools | Backend, Frontend, QA |
| `editor` | strands_tools | Backend, Frontend (editar código existente) |
| `shell` | strands_tools | QA (correr tests), Backend (migrations) |
| `python_repl` | strands_tools | QA (ejecutar tests inline) |
| `current_time` | strands_tools | Orquestador (timestamps en logs) |
| `jira_get_issue` | MCP (mcp-atlassian) | Orquestador |
| `jira_update_issue` | MCP (mcp-atlassian) | Orquestador |
| `jira_add_comment` | MCP (mcp-atlassian) | Orquestador |
| `jira_search_issues` | MCP (mcp-atlassian) | Orquestador |
| `github_create_branch` | MCP (github) | Orquestador |
| `github_create_pull_request` | MCP (github) | Orquestador |

### 4.3 Definición de Agentes

Cada agente tiene un rol claro, system prompt acotado, y tools específicos. Los MCP clients se pasan directamente — Strands maneja su lifecycle.

#### Agente Arquitecto (Orquestador)

Recibe el ticket Jira (via MCP), analiza requisitos, descompone en subtareas y coordina a los demás agentes (pasados como tools).

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
1. Use jira_get_issue to read the ticket details
2. Use jira_update_issue to set status to "In Progress"
3. Use jira_add_comment to log that work has started
4. Analyze requirements and determine which agents to call
5. Call backend_agent and/or frontend_agent with specific tasks
6. Call qa_agent to validate the generated code
7. Use shell to run: git checkout -b agent/<ticket-id> && git add . && git commit
8. Use github_create_pull_request to create the PR
9. Use jira_add_comment to post the PR link
10. If any agent fails twice, use jira_update_issue to set "Blocked" and jira_add_comment with error

Available agents:
- backend_agent: Server-side code, APIs, database models, business logic
- frontend_agent: UI components, pages, client-side logic
- qa_agent: Unit tests, integration tests, runs test suites
""",
    tools=[
        *ORCHESTRATOR_TOOLS,    # jira_mcp, github_mcp
        current_time,
        shell,                  # para git operations
        backend_agent,
        frontend_agent,
        qa_agent,
    ],
)
```

#### Agente Backend Developer

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

#### Agente Frontend Developer

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

#### Agente QA

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

### 4.4 Alternativa: Graph Builder para flujos secuenciales

Para tickets donde el flujo siempre es lineal (Backend → Frontend → QA), puedes usar `GraphBuilder`:

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

### 4.5 Pipeline Completo

```python
import uuid

async def launch_agent_pipeline(ticket_id: str) -> str:
    """Lanza el pipeline de agentes para un ticket Jira."""
    session_id = str(uuid.uuid4())

    # Guardar sesión en DB
    await save_session(session_id, ticket_id, status="started")

    # Emitir evento al dashboard
    await emit_event(session_id, "pipeline_started", {"ticket_id": ticket_id})

    try:
        # El orquestador hace TODO via tools (MCP + strands_tools):
        # - Lee el ticket de Jira (jira_get_issue)
        # - Lo transiciona a "In Progress" (jira_update_issue)
        # - Delega a agentes dev (backend_agent, frontend_agent, qa_agent)
        # - Crea branch y PR (shell + github_create_pull_request)
        # - Comenta en Jira con el link al PR (jira_add_comment)
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

## 5. Human-in-the-Loop: Review y CI/CD

El código generado por agentes **nunca va directo a producción**. El flujo de aprobación:

```
Agentes generan código
       ↓
Git branch: agent/proj-123
       ↓
Pull Request automático (GitHub/CodeCommit)
       ↓
CI/CD Pipeline se activa:
  ├── Linting (ruff, eslint)
  ├── Tests unitarios (pytest, vitest)
  ├── Tests integración
  ├── Security scan (bandit, npm audit)
  └── Build check
       ↓
  ┌─────────────────────────┐
  │  HUMAN REVIEW REQUIRED  │
  │                         │
  │  - Code review del PR   │
  │  - Verificar calidad    │
  │  - Aprobar o rechazar   │
  └─────────────────────────┘
       ↓ (si aprobado)
  Merge → Deploy a staging → Deploy a prod
```

### Configuración de branch protection

```yaml
# GitHub branch protection (configurar via UI o API)
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

### CI/CD Genérico (CodeBuild/GitHub Actions)

```yaml
# buildspec.yml para CodeBuild / .github/workflows/ci.yml
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

## 6. Modelo de Datos

PostgreSQL 16 con SQLAlchemy async.

```sql
-- Sesiones de pipeline
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

-- Eventos de agentes (alimentan el dashboard via Socket.IO)
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

## 7. Dashboard de Monitoreo (MVP)

### 7.1 Arquitectura

```
PostgreSQL → Socket.IO (FastAPI) → React Dashboard
                                               ↓
                                          Canvas 2D (SVG)
                                          AgentFigures
                                          LogPanel
                                          MetricsPanel
```

### 7.2 Comunicación en Tiempo Real (Socket.IO)

```python
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

async def emit_event(session_id: str, event_type: str, payload: dict):
    """Emite evento a todos los clientes conectados al room de la sesión."""
    await sio.emit("agent_event", {
        "type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }, room=session_id)

@sio.event
async def join_session(sid, data):
    """Cliente se une al room de una sesión para recibir eventos."""
    sio.enter_room(sid, data["session_id"])
    state = await get_session_state(data["session_id"])
    await sio.emit("state_sync", state, to=sid)
```

#### Formato de Mensajes

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

Tipos de eventos: `agent_state_change`, `agent_log`, `task_assigned`, `task_completed`, `error`, `pipeline_started`, `pipeline_completed`, `pr_created`.

### 7.3 Sistema de Figuras 2D (Sprites SVG)

Cada agente se representa como un personaje SVG simple con animaciones CSS por estado.

#### Estados Visuales

| Estado | Visual | Animación CSS |
|---|---|---|
| `idle` | Personaje neutral, color base | `animate-bob` (float suave vertical 2px, 2s) |
| `thinking` | Burbuja de pensamiento con "..." | `animate-pulse` (opacidad pulsante, 1s) |
| `working` | Partículas de actividad, herramienta activa | `animate-work` (movimiento de manos, 0.5s) |
| `waiting` | Reloj de arena o "?" sobre la cabeza | `animate-wait` (opacidad lenta, 3s) |
| `success` | Check verde, expresión feliz | `animate-bounce` (rebote, 0.5s) |
| `error` | "!" rojo, expresión preocupada | `animate-shake` (vibración horizontal, 0.3s) |

#### Diseño por Rol

| Agente | Color Primario | Elemento Distintivo |
|---|---|---|
| **Arquitecto** | Azul navy `#1E3A5F` | Sombrero/casco + blueprint |
| **Backend** | Verde esmeralda `#0D7377` | Terminal/prompt + auriculares |
| **Frontend** | Coral `#FF6B6B` | Paleta de colores + gafas redondas |
| **QA** | Naranja `#F0932B` | Lupa gigante + bata de lab |

#### Componente React

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

#### Conexiones entre Agentes

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

### 7.4 Layout del Dashboard

```
┌──────────────┬──────────────────────────────┬──────────────┐
│              │                              │              │
│  Task List   │     Canvas Central (60%)     │   Log Panel  │
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

### 7.5 Componentes del Dashboard

| Componente | Responsabilidad |
|---|---|
| `AgentCanvas` | SVG canvas central, renderiza figuras y conexiones |
| `AgentFigure` | Sprite individual con estado y animación |
| `TaskPanel` | Lista de tareas del ticket, estado de cada una |
| `LogPanel` | Logs en tiempo real, filtrable por agente |
| `MetricsBar` | Tokens usados, tiempo, archivos generados, estado de tests |
| `ConnectionStatus` | Estado de conexión Socket.IO con auto-reconnect |

---

## 8. Seguridad y Guardrails

### Seguridad
- API keys en `.env` (git-ignored). En producción, inyectar como secrets del proveedor cloud
- Agentes ejecutan código en **directorios aislados** (`/app/workspaces/<ticket-id>/`)
- Branch protection rules impiden merge sin review
- MCP servers corren como subprocesos del backend, no expuestos externamente

### Guardrails Anti-Loop y Control de Billing

> **CRITICO para PoC y producción.** Los agentes pueden entrar en loops infinitos que consumen tokens sin parar. Estos guardrails son obligatorios.

#### Límites por agente

```python
from strands import Agent

agent = Agent(
    model=minimax,
    system_prompt="...",
    tools=[...],
)
```

#### Configuración de límites

| Guardrail | Valor Default | Descripción |
|---|---|---|
| **Timeout por agente** | 5 min | El agente se cancela si excede este tiempo |
| **Max iteraciones (tool calls)** | 20 | Máximo de tool calls por invocación de agente |
| **Max iteraciones orquestador** | 50 | El orquestador tiene más margen porque coordina |
| **Token budget por sesión** | 100k tokens | Se trackea y corta si se excede |
| **Max archivos por agente** | 15 | Evita que un agente cree archivos infinitamente |
| **Max tamaño de archivo** | 500 líneas | Si un agente genera más, se corta y reporta error |

#### Implementación del token tracker

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

#### Qué pasa cuando se excede un límite

1. El agente se detiene inmediatamente
2. Se guarda el estado parcial en la DB
3. Se emite evento `budget_exceeded` al dashboard
4. Se comenta en Jira: "Agent pipeline paused — budget exceeded. Manual intervention required."
5. El ticket se transiciona a "Blocked"

### Manejo de Errores
- Retry con backoff exponencial en llamadas a MiniMax API
- Circuit breaker si MiniMax está caído (notifica y pausa)
- Timeout por agente (configurable, default 5 min)
- Si un agente falla 2 veces, el orquestador marca el ticket como "Blocked" en Jira

### Costos
- **MiniMax M2.7**: consultar pricing actual en https://platform.minimax.io/subscribe/token-plan
- **Infra**: PostgreSQL + Docker containers — costo fijo y predecible
- **Sin servicios serverless** que escalen inesperadamente
- Los guardrails de token budget son la principal protección contra billing sorpresa

### Observabilidad
- Logs en stdout (structured JSON) + PostgreSQL (tabla `agent_events`) + Socket.IO dashboard
- En producción, agregar collector de logs (Loki, ELK, o el nativo del cloud provider)

---

## 9. Runbook Operacional

### 9.1 Operaciones Comunes

#### Iniciar el sistema (local)

```bash
# 1. Verificar que Docker esté corriendo
docker --version

# 2. Iniciar todos los servicios
docker compose up -d

# 3. Verificar estado de los servicios
docker compose ps

# 4. Ver logs en tiempo real
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 5. Verificar conexión a Jira MCP
docker compose exec backend uvx mcp-atlassian --info
```

#### Detener el sistema

```bash
# Detener todos los servicios (preserva datos)
docker compose stop

# Detener y eliminar volúmenes (BORRA DATOS)
docker compose down -v
```

#### Reiniciar un servicio específico

```bash
docker compose restart backend
docker compose restart frontend
docker compose restart db
```

---

### 9.2 Verificación de Salud

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

#### Checklist de salud del pipeline

| Componente | Verificación | Comando |
|---|---|---|
| **PostgreSQL** | Conexión activa | `docker compose exec db psql -U agent -d multi_agent -c "SELECT 1"` |
| **MiniMax API** | API responde | `curl -s -o /dev/null -w "%{http_code}" https://api.minimax.io/v1/models` |
| **Jira MCP** | Tool disponible | `docker compose exec backend python -c "from mcp import stdio_client; print('MCP OK')"` |
| **GitHub MCP** | Token válido | `gh auth status` |
| **strands_tools** | Herramientas cargan | `python -c "from strands_tools import file_read, file_write; print('OK')"` |

---

### 9.3 Manejo de Incidentes

#### Pipeline fallido — Ticket bloqueado

**Síntoma**: El ticket en Jira está en estado "Blocked" o el PR no se creó.

**Diagnóstico**:
```bash
# 1. Ver logs del backend
docker compose logs backend --tail=100 | grep -i error

# 2. Verificar si el workspace existe
ls -la workspaces/

# 3. Ver estado de la sesión en DB
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT id, ticket_id, status, error FROM agent_sessions ORDER BY created_at DESC LIMIT 5;"
```

**Resolución**:
```bash
# 1. Limpiar workspace del ticket
rm -rf workspaces/<ticket-id>/

# 2. Resetear estado en Jira (manual o via UI)

# 3. Re-lanzar pipeline manualmente
curl -X POST http://localhost:8000/trigger/<ticket-id>
```

#### Error de autenticación Jira/GitHub

**Síntoma**: `AuthenticationError` en logs.

**Diagnóstico**:
```bash
# Verificar variables de entorno
docker compose exec backend env | grep -E "(JIRA|GITHUB)"

# Testear token de Jira
docker compose exec backend curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_URL/rest/api/2/myself" | head -c 200

# Testear token de GitHub
gh auth status
```

**Resolución**:
```bash
# Actualizar secrets en .env
# Reiniciar backend
docker compose restart backend
```

#### Budget exceeded (tokens/iteraciones)

**Síntoma**: `BudgetExceededError` en logs, ticket en "Blocked".

**Diagnóstico**:
```bash
# Ver consumo de tokens
docker compose logs backend | grep -i "budget\|tokens"

# Ver último evento de budget
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT * FROM agent_events WHERE event_type = 'budget_exceeded' ORDER BY created_at DESC LIMIT 3;"
```

**Resolución**:
```bash
# Aumentar límites en config (temporalmente)
# O limpiar sesión y reintentar
docker compose exec db psql -U agent -d multi_agent -c \
  "DELETE FROM agent_events WHERE session_id = '<session-id>';"
```

#### MiniMax API no responde

**Síntoma**: `ConnectionError` o timeout en llamadas al LLM.

**Diagnóstico**:
```bash
# Testear conectividad
curl -v https://api.minimax.io/v1/models \
  -H "Authorization: Bearer $MINIMAX_API_KEY" 2>&1 | head -20

# Verificar rate limits
curl -s https://api.minimax.io/v1/usage \
  -H "Authorization: Bearer $MINIMAX_API_KEY"
```

**Resolución**:
```bash
# Esperar y reintentar (backoff automático si está implementado)
# Si el problema persiste, verificar status de MiniMax
# Alternativa: usar OpenRouter como fallback
```

#### Modelo alcanza 70% de usage (switch dinámico)

**Síntoma**: Se alcanzó ~70% del quota de tokens del modelo actual.

**Modelos configurados**:
- **Primary**: `MiniMax-M2.7` via api.minimax.io
- **Fallback**: `MiniMax-M2.7` via OpenRouter

**Resolución (switch manual a fallback)**:
```bash
# Cambiar MINIMAX_API_URL en .env a OpenRouter
sed -i 's|MINIMAX_API_URL=.*|MINIMAX_API_URL=https://openrouter.ai/api/v1|' .env
docker compose restart backend
```

---

### 9.4 Recovery Procedures

#### Disaster Recovery — Pérdida de PostgreSQL

```bash
# 1. Verificar que el volumen persiste
docker compose inspect db | grep -A5 "Mounts"

# 2. Si hay backup, restaurar
docker compose exec db psql -U agent -d multi_agent < backup.sql

# 3. Si no hay backup y hay workspaces:
#    Los agentes pueden regenerar el código desde el PR
#    Solo se pierden eventos/histórico
```

#### Recovery de Workspace corrupto

```bash
# 1. Identificar workspace problemáticos
ls -la workspaces/

# 2. Regenerar desde PR
#    - El PR contiene todo el código generado

# 3. Limpiar workspace
rm -rf workspaces/<ticket-id>/
```

---

### 9.5 Comandos de Debugging

```bash
# Ver todos los eventos de una sesión
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT agent_id, event_type, created_at FROM agent_events \
   WHERE session_id = '<session-id>' ORDER BY created_at;"

# Ver logs de un agente específico
docker compose logs -f backend 2>&1 | grep "backend_agent"

# Ver consumo de recursos
docker stats

# Ver variables de entorno cargadas en backend
docker compose exec backend env | sort

# Acceder a shell en el container
docker compose exec backend /bin/bash

# Verificar versión de dependencias
docker compose exec backend pip list | grep -E "(strands|fastapi|socketio)"

# Testar MCP manualmente
docker compose exec backend python -c "
from mcp import stdio_client, StdioServerParameters
print('MCP client importado OK')
"
```

---

### 9.6 Contactos y Escalación

| Nivel | Responsable | Cuando escalar |
|---|---|---|
| **L1** | DevOps on-call | Pipeline fallido, errores de conexión |
| **L2** | Backend Lead | Bugs en agentes, memory leaks, performance |
| **L3** | Architect | Diseño de agentes, cambios en flow, incidents mayores |

---

## 10. Futuros / Deseables

> Las siguientes funcionalidades **no son parte del MVP** pero están contempladas para iteraciones futuras.

### 10.1 Agentes de Remediación de Producción

Usar agentes para **diagnosticar y resolver automáticamente errores de producción**:

- CloudWatch Alarm → EventBridge → Lambda → Strands Orchestrator
- Agente de Diagnóstico: analiza logs, métricas, traces del error
- Agente de Remediación: ejecuta acciones correctivas (escalar instancia, rollback, restart servicio)
- Agente de Validación: verifica que el fix funcionó
- Requiere: IAM roles con permisos de ejecución, guardrails estrictos, runbooks predefinidos

### 10.2 Agente de DevOps

Agente que genera y mantiene IaC (CDK/CloudFormation), Dockerfiles, y pipelines CI/CD.

### 10.3 Agente de Documentación

Genera y mantiene README, API docs, y guías de contribución a partir del código generado.

### 10.4 Aprendizaje de Reviews

Almacenar feedback de code reviews humanos para que los agentes mejoren con el tiempo (fine-tuning o RAG sobre comentarios de PR).

### 10.5 Dashboard Avanzado

- Sprite sheets con pixel art y animaciones avanzadas (referencia: [NightCityVerse](https://github.com/eruizpy/nightcityverse))
- Temas claro/oscuro
- Skins configurables por agente
- Métricas históricas y analytics

### 10.6 AgentCore con Full AWS (Alternative Architecture)

**Alternativa futura para equipos ya invertidos en AWS.**

| Criterio | Strands SDK (MVP) | Bedrock AgentCore (Futuro) |
|---|---|---|
| LLM externo (MiniMax) | **Si** — `OpenAIModel` provider | No — solo modelos Bedrock |
| Control del flujo | Total, es tu código Python | Managed, menos flexibilidad |
| Costo de infra | Solo ECS + LLM API | AgentCore Runtime + LLM |
| Multi-agent patterns | Agents-as-tools, GraphBuilder, Swarm | Limitado a Bedrock agents |
| Curva de aprendizaje | Moderada, buen docs | Baja pero menos flexible |
| Demo-friendliness | **Alto** — puedes mostrar el código | Más "caja negra" |
| Vendor lock-in | **Bajo** — cloud-agnostic | Alto — solo AWS |

**Cuándo considerar migrar a AgentCore:**
- Equipo ya tiene experiencia profunda con AWS
- Se necesita integración nativa con Bedrock (Claude, etc.)
- Se prioriza simplicidad de gestión sobre control
- El costo de AgentCore Runtime es aceptable

**Nota:** La arquitectura actual (Strands + Docker + PostgreSQL) está diseñada para ser cloud-agnostic. Si en el futuro se migra a Bedrock, Strands soporta ambos sin cambio de arquitectura significativa.

#### DynamoDB como alternativa a PostgreSQL (AWS)

Para deploy en AWS, PostgreSQL puede substituirse por DynamoDB:

| Tabla | PK | SK | Uso |
|---|---|---|---|
| `AgentSessions` | `session_id` | `#metadata` | Estado del pipeline |
| `AgentEvents` | `session_id` | `timestamp#event_id` | Eventos para dashboard |
| GSI: `TicketIndex` | `ticket_id` | `created_at` | Buscar por ticket |

La capa de acceso a datos se abstrae con un **repository pattern** para que el switch PostgreSQL → DynamoDB sea transparente.

```
DynamoDB Streams → Lambda → Socket.IO (FastAPI) → React Dashboard
```

---

## 11. Recursos de Referencia

### Strands SDK
- [Strands Agents SDK — Docs](https://strandsagents.com)
- [Strands — Multi-Agent Patterns (agents-as-tools)](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/multi-agent/agents-as-tools.mdx)
- [Strands — GraphBuilder](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/multi-agent/graph.mdx)
- [Strands — MCP Integration](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/tools/mcp-tools.mdx)
- [Strands Tools (file_read, file_write, editor, shell, etc.)](https://github.com/strands-agents/tools)
- [Strands — Custom Model Providers](https://github.com/strands-agents/docs/blob/main/src/content/docs/user-guide/concepts/model-providers/custom_model_provider.mdx)

### MCP Servers
- [mcp-atlassian (Jira + Confluence MCP server)](https://github.com/sooperset/mcp-atlassian)
- [Atlassian Remote MCP Server (oficial)](https://www.atlassian.com/blog/announcements/remote-mcp-server)
- [GitHub MCP Server (@modelcontextprotocol/server-github)](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

### LLM
- [MiniMax API — OpenAI Compatible Endpoint](https://platform.minimax.io/docs/api-reference/text-openai-api)
- [MiniMax Token Plans](https://platform.minimax.io/subscribe/token-plan)
- [OpenRouter — MiniMax M2.7](https://openrouter.ai/minimax/minimax-m2.7)

### Referencia de Arquitectura
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [NightCityVerse — Visual runtime para agentes AI](https://github.com/eruizpy/nightcityverse)
