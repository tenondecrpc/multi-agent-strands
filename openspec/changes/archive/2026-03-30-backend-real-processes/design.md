## Context

The MVP backend has basic agent scaffolds but lacks real async task execution, workflow orchestration, and state management. Current limitations prevent handling actual Jira ticket workflows with proper error recovery and agent collaboration.

## Goals / Non-Goals

**Goals:**
- Implement Celery-based task queue with Redis broker for async job execution
- Define ticket processing pipeline with stage-based state machine
- Create AgentManager for orchestrating multi-agent sessions and handoffs
- Build event-driven communication using in-memory event bus with SSE subscriptions
- Add state persistence for ticket states and agent sessions

**Non-Goals:**
- Distributed locking (future enhancement with Redis distributed-lock)
- Horizontal scaling of Celery workers (single instance for MVP)
- Webhook-based Jira integration (using polling for MVP)
- Complex saga patterns for distributed transactions

## Decisions

### 1. Celery over Raw asyncio

**Decision**: Use Celery with Redis broker instead of raw asyncio.create_task()

**Rationale**: Celery provides:
- Built-in retry logic and error handling
- Task result backend and state tracking
- Priority queuing out of the box
- Worker management and monitoring
- Proven production-grade solution

**Alternative Considered**: Raw asyncio with in-memory queue
- Rejected because it lacks persistence, retry mechanisms, and worker management

### 2. In-Memory Event Bus over Message Broker

**Decision**: Use in-memory event bus with SSE for real-time subscriptions

**Rationale**:
- SSE is simpler for browser clients than WebSocket
- In-memory is sufficient for single-backend MVP
- Can migrate to Redis pub/sub later if scaling requires

**Alternative Considered**: Redis pub/sub
- Deferred because adds complexity without immediate benefit for MVP

### 3. SQLAlchemy Async for State Persistence

**Decision**: Use SQLAlchemy async with existing PostgreSQL setup

**Rationale**:
- Consistent with existing codebase patterns
- Async support for non-blocking DB operations
- JSON columns for flexible artifact storage

**Alternative Considered**: Redis for state
- Rejected because PostgreSQL provides better query capabilities and durability

### 4. Stage-Based Ticket Processing

**Decision**: Use enum-based stage machine (NEW → DONE)

**Rationale**:
- Simple and explicit state transitions
- Easy to audit and debug
- Jira ticket workflow maps naturally to stages

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Celery worker failures lose in-flight tasks | Configure `task_acks_late=True` and persistent result backend |
| Event bus memory growth with many subscribers | Limit event retention and implement cleanup |
| Database connection pool exhaustion | Use async session with proper cleanup and connection limits |
| Agent handoff context loss | Persist context to database before handoff |

## Open Questions

1. Should agent streaming use Server-Sent Events (SSE) or WebSockets?
   - Current decision: SSE for simplicity
2. How to handle long-running agent tasks that exceed timeout?
   - Current decision: Split into smaller subtasks with checkpointing
3. Should we implement optimistic locking for concurrent ticket updates?
   - Deferred to future enhancement with redis distributed-lock
