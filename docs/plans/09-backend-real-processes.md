# 10. Real Backend Processes

> **Status**: Planned — Part of Backend Implementation objective

## Objective

Implement real, production-ready backend processes that handle actual Jira ticket workflow, agent orchestration, and task execution with proper async handling, state management, and error recovery.

## Current State

The MVP backend has basic agent definitions and tool scaffolds, but lacks:
- Real ticket processing workflow orchestration
- Proper async task queue and job management
- Agent handoff and collaboration protocols
- State persistence and recovery mechanisms
- Error handling with retry logic
- Event-driven architecture for agent communication

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Jira      │  │   Task      │  │    Event               │  │
│  │   Poller    │──▶│   Queue     │──▶│    Bus                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                    │                   │
│         ▼                                    ▼                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Ticket    │  │   Agent     │  │    State                │  │
│  │   Service   │──▶│   Manager   │──▶│    Store                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Architect  │  │  Backend    │  │    Frontend             │  │
│  │  Agent      │  │  Agent       │  │    Agent                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
│                  ┌─────────────┐                                │
│                  │     QA      │                                │
│                  │    Agent     │                                │
│                  └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Task Queue System

Implement a robust task queue using background tasks:

```python
from celery import Celery
from typing import TypedDict, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class TaskPriority(str, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class Task(TypedDict):
    id: str
    ticket_id: str
    agent_type: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    max_retries: int
    error: Optional[str]
    result: Optional[dict]
```

### 2. Ticket Processing Pipeline

Define the complete ticket lifecycle:

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class TicketStage(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_ANALYSIS = "in_analysis"
    IN_DEVELOPMENT = "in_development"
    IN_REVIEW = "in_review"
    IN_TESTING = "in_testing"
    DONE = "done"
    BLOCKED = "blocked"

class TicketProcessing(BaseModel):
    ticket_id: str
    jira_key: str
    current_stage: TicketStage
    assigned_agent: Optional[str]
    context_window: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    blocked_reason: Optional[str] = None

class ProcessingResult(BaseModel):
    ticket_id: str
    stage: TicketStage
    success: bool
    summary: str
    artifacts: dict[str, str]
    next_actions: list[str]
    handoff_to: Optional[str]
```

### 3. Agent Manager

Orchestrate multi-agent collaboration:

```python
from dataclasses import dataclass, field
from typing import Callable, Awaitable
from collections.abc import AsyncIterator

@dataclass
class AgentConfig:
    name: str
    model: str
    system_prompt: str
    tools: list[str]
    max_iterations: int = 10
    timeout_seconds: int = 300

@dataclass
class AgentContext:
    ticket_id: str
    current_task: str
    previous_results: dict[str, str]
    shared_state: dict[str, str]
    handoff_log: list[dict]

class AgentManager:
    def __init__(self):
        self.agents: dict[str, AgentConfig] = {}
        self.active_sessions: dict[str, AgentContext] = {}
    
    async def start_session(self, ticket_id: str, agent_type: str) -> str:
        session_id = f"{ticket_id}-{agent_type}-{uuid4()}"
        self.active_sessions[session_id] = AgentContext(
            ticket_id=ticket_id,
            current_task="",
            previous_results={},
            shared_state={},
            handoff_log=[]
        )
        return session_id
    
    async def execute_agent(
        self, 
        session_id: str, 
        task: str
    ) -> AsyncIterator[str]:
        context = self.active_sessions[session_id]
        context.current_task = task
        
        agent = self.agents.get(context.current_task)
        if not agent:
            raise ValueError(f"Unknown agent type")
        
        async for token in agent.stream_run(task, context):
            yield token
    
    async def handoff(
        self, 
        session_id: str, 
        from_agent: str, 
        to_agent: str,
        summary: str
    ) -> None:
        context = self.active_sessions[session_id]
        context.handoff_log.append({
            "from": from_agent,
            "to": to_agent,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
```

### 4. Event Bus

Implement event-driven communication:

```python
from typing import TypedDict, Literal
from datetime import datetime

class EventType(str, Enum):
    TICKET_RECEIVED = "ticket:received"
    TICKET_UPDATED = "ticket:updated"
    TICKET_STAGE_CHANGED = "ticket:stage_changed"
    AGENT_STARTED = "agent:started"
    AGENT_COMPLETED = "agent:completed"
    AGENT_FAILED = "agent:failed"
    AGENT_HANDOFF = "agent:handoff"
    ARTIFACT_CREATED = "artifact:created"
    COMMENT_ADDED = "comment:added"

class Event(TypedDict):
    id: str
    type: EventType
    ticket_id: str
    agent_id: Optional[str]
    payload: dict
    timestamp: datetime

class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    async def publish(self, event: Event) -> None:
        handlers = self._subscribers.get(event["type"], [])
        for handler in handlers:
            await handler(event)
```

### 5. State Persistence

Persist agent and ticket state to database:

```python
from sqlalchemy import Column, String, JSON, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID

class TicketStateModel(Base):
    __tablename__ = "ticket_states"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    jira_key: Mapped[str] = mapped_column(String(20), index=True)
    current_stage: Mapped[str] = mapped_column(String(20))
    assigned_agent: Mapped[str] = mapped_column(String(50), nullable=True)
    context_window: Mapped[dict] = mapped_column(JSON)
    artifacts: Mapped[dict] = mapped_column(JSON)
    handoff_history: Mapped[list] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

class AgentSessionModel(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String(50), index=True)
    agent_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    current_task: Mapped[str] = mapped_column(String(500))
    result: Mapped[dict] = mapped_column(JSON, nullable=True)
    error: Mapped[str] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
```

### 6. Error Handling & Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AgentExecutionError(Exception):
    def __init__(self, agent: str, task: str, original_error: Exception):
        self.agent = agent
        self.task = task
        self.original_error = original_error
        super().__init__(f"{agent} failed on {task}: {original_error}")

class RetryableError(Exception):
    pass

class NonRetryableError(Exception):
    pass

RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_wait": 5,
    "max_wait": 60,
    "multiplier": 2
}

async def execute_with_retry(
    agent_type: str,
    task: str,
    context: AgentContext
) -> dict:
    for attempt in range(RETRY_CONFIG["max_attempts"]):
        try:
            result = await agent_manager.execute_agent(
                context.session_id,
                task
            )
            return {"success": True, "result": result}
        except RetryableError as e:
            if attempt == RETRY_CONFIG["max_attempts"] - 1:
                raise AgentExecutionError(agent_type, task, e)
            wait_time = min(
                RETRY_CONFIG["initial_wait"] * (RETRY_CONFIG["multiplier"] ** attempt),
                RETRY_CONFIG["max_wait"]
            )
            await asyncio.sleep(wait_time)
        except NonRetryableError as e:
            raise AgentExecutionError(agent_type, task, e)
```

## Ticket Processing Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     TICKET PROCESSING FLOW                          │
└──────────────────────────────────────────────────────────────────────┘

[Jira Webhook] ──or── [Poller]
       │
       ▼
┌─────────────────┐
│  Ticket Received │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Validate &      │────▶│  Create/Update   │
│  Enrich Ticket   │     │  TicketState     │
└────────┬────────┘     └────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐
│  Triage by       │     │  Emit           │
│  Architect       │────▶│  ticket:stage   │
└────────┬────────┘     │  _changed        │
         │               └────────┬────────┘
         │                        │
         ▼                        │
┌─────────────────┐              │
│  Assign to       │              │
│  appropriate     │              │
│  agent           │              │
└────────┬────────┘              │
         │                        │
         ├────────────────────────┤
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌─────────────────┐
│  Backend/       │     │  Frontend/      │
│  Development     │     │  UI Tasks       │
└────────┬────────┘     └────────┬────────┘
         │                        │
         ├────────────────────────┤
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌─────────────────┐
│  QA Agent       │────▶│  Review         │
│  Testing        │     │  Comments        │
└────────┬────────┘     └────────┬────────┘
         │                        │
         └───────────┬────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Handoff to     │
            │  Human Review   │
            │  (if needed)     │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Done / Closed  │
            └─────────────────┘
```

## API Endpoints

### Ticket Management

```python
@router.post("/tickets/{ticket_id}/process")
async def process_ticket(ticket_id: str) -> ProcessingResult:
    """
    Trigger full processing pipeline for a ticket.
    """
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    result = await ticket_pipeline.execute(ticket_id)
    return result

@router.post("/tickets/{ticket_id}/stage")
async def update_ticket_stage(
    ticket_id: str,
    stage: TicketStage,
    comment: Optional[str] = None
) -> TicketState:
    """
    Manually update ticket stage with optional comment.
    """
    state = await ticket_service.update_stage(ticket_id, stage)
    if comment:
        await jira_client.add_comment(ticket_id, comment)
    await event_bus.publish(Event(
        id=str(uuid4()),
        type=EventType.TICKET_STAGE_CHANGED,
        ticket_id=ticket_id,
        agent_id=None,
        payload={"stage": stage, "comment": comment},
        timestamp=datetime.utcnow()
    ))
    return state
```

### Agent Session Management

```python
@router.post("/sessions")
async def create_session(
    ticket_id: str,
    agent_type: AgentType
) -> AgentSession:
    """
    Create a new agent session for a ticket.
    """
    session_id = await agent_manager.start_session(ticket_id, agent_type)
    return AgentSession(session_id=session_id, ticket_id=ticket_id, agent_type=agent_type)

@router.post("/sessions/{session_id}/execute")
async def execute_task(
    session_id: str,
    task: str
) -> AsyncGenerator[str, None]:
    """
    Execute a task within an existing agent session.
    Streams tokens as they are generated.
    """
    async for token in agent_manager.execute_agent(session_id, task):
        yield token

@router.post("/sessions/{session_id}/handoff")
async def handoff_session(
    session_id: str,
    to_agent: AgentType,
    summary: str
) -> AgentSession:
    """
    Hand off a session from one agent to another.
    """
    current = await agent_manager.get_session(session_id)
    await agent_manager.handoff(session_id, current.agent_type, to_agent, summary)
    return await agent_manager.get_session(session_id)
```

### Event Subscription

```python
@router.get("/events/{ticket_id}")
async def subscribe_to_events(
    ticket_id: str,
    last_event_id: Optional[str] = None
) -> AsyncGenerator[Event, None]:
    """
    SSE endpoint for subscribing to ticket events.
    """
    async for event in event_bus.subscribe_ticket(ticket_id, last_event_id):
        yield event
```

## File Structure

```
backend/app/
├── api/
│   ├── routes/
│   │   ├── tickets.py          # Ticket endpoints
│   │   ├── sessions.py         # Agent session endpoints
│   │   └── events.py           # SSE event subscriptions
│   └── dependencies.py         # FastAPI dependencies
├── core/
│   ├── task_queue.py           # Celery task definitions
│   ├── event_bus.py            # Event system implementation
│   ├── state_store.py           # State persistence layer
│   └── config.py               # Configuration management
├── services/
│   ├── ticket_service.py        # Ticket business logic
│   ├── jira_service.py          # Jira API integration
│   ├── agent_manager.py         # Multi-agent orchestration
│   └── artifact_service.py      # Artifact storage/retrieval
├── agents/
│   ├── base.py                  # Base agent class
│   ├── architect.py             # Architect agent implementation
│   ├── backend.py               # Backend agent implementation
│   ├── frontend.py              # Frontend agent implementation
│   └── qa.py                    # QA agent implementation
├── models/
│   ├── ticket_state.py          # Ticket state SQLAlchemy model
│   ├── agent_session.py         # Agent session model
│   └── events.py                # Event log model
└── schemas/
    ├── ticket.py                 # Ticket Pydantic schemas
    ├── session.py                # Session Pydantic schemas
    └── events.py                 # Event Pydantic schemas
```

## Dependencies

```bash
# Core dependencies
celery[redis]==5.3.6          # Task queue
redis==5.0.1                  # Redis for Celery broker
python-multipart==0.0.6       # SSE support
sse-starlette==1.8.2          # Server-Sent Events
tenacity==8.2.3               # Retry logic
structlog==23.2.0             # Structured logging

# Optional: for distributed locking
redis distributed-lock==1.0.2  # Optimistic locking for tickets
```

## Testing Strategy

```python
# tests/test_ticket_pipeline.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_jira_client():
    client = MagicMock()
    client.get_ticket = AsyncMock(return_value=mock_jira_ticket())
    client.add_comment = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_ticket_processing_flow(mock_jira_client):
    pipeline = TicketPipeline(jira_client=mock_jira_client)
    result = await pipeline.execute("PROJ-123")
    
    assert result.success is True
    assert result.stage == TicketStage.DONE
    assert len(result.artifacts) > 0

@pytest.mark.asyncio
async def test_agent_handoff():
    manager = AgentManager()
    session_id = await manager.start_session("PROJ-123", "backend")
    
    await manager.handoff(session_id, "backend", "qa", "Code complete")
    
    context = manager.active_sessions[session_id]
    assert len(context.handoff_log) == 1
    assert context.handoff_log[0]["to"] == "qa"
```

## Reference

- [Celery Distributed Task Queue](https://docs.celeryproject.org/)
- [Event-Driven Architecture Patterns](https://event-driven.io/)
- [Strands Agents SDK](https://github.com/strands-agents/strands-python)
- [Server-Sent Events with FastAPI](https://www.starlette.io/)
