## Context

The system needs to store the state of the multi-agent pipeline when triggered by a Jira ticket. This ensures we can resume, monitor, and query historical data for metrics and the real-time dashboard. The architecture mandates using PostgreSQL with SQLAlchemy (asyncpg). Since we are using FastAPI, an async ORM approach is optimal for high concurrency without blocking the event loop.

## Goals / Non-Goals

**Goals:**
- Implement SQLAlchemy setup with async engine and session maker.
- Create initial models: `AgentSession` and `AgentEvent`.
- Set up Alembic to manage database migrations.
- Establish relationships between `AgentSession` and `AgentEvent`.

**Non-Goals:**
- Implementing the REST API endpoints or WebSocket server (this is just the data layer).
- Adding complex domain logic or custom query repositories (only basic SQLAlchemy setup).

## Decisions

- **Async SQLAlchemy**: Use `sqlalchemy.ext.asyncio` with `asyncpg`. This aligns with FastAPI's async nature.
- **UUID Primary Keys**: Use `UUID` for primary keys. It's safer for distributed systems and makes IDs unguessable, avoiding potential enumeration issues.
- **Alembic**: We will use Alembic for all schema migrations. An initial migration will be created that defines the `agent_sessions` and `agent_events` tables.
- **Relationships**: `AgentSession` will have a one-to-many relationship with `AgentEvent`.

## Risks / Trade-offs

- [Risk] Async DB operations can be tricky to debug compared to sync. → Use clear logging and strict typing (`Mapped` from SQLAlchemy 2.0).
- [Risk] Alembic async support requires specific configuration in `env.py`. → Ensure the generated `env.py` uses `run_migrations_online` with async capabilities.
