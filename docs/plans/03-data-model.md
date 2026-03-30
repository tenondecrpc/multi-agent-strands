# 3. Data Model (MVP) ✅

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

## SQLAlchemy Models

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
