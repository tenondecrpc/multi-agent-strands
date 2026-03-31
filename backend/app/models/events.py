import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import DateTime, Enum as SQLEnum, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EventType(str, Enum):
    TICKET_RECEIVED = "TICKET_RECEIVED"
    TICKET_UPDATED = "TICKET_UPDATED"
    TICKET_STAGE_CHANGED = "TICKET_STAGE_CHANGED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    AGENT_HANDOFF = "AGENT_HANDOFF"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    COMMENT_ADDED = "COMMENT_ADDED"
    LLM_CREDIT_EXHAUSTED = "LLM_CREDIT_EXHAUSTED"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType), nullable=False, index=True
    )
    ticket_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_events_ticket_id", "ticket_id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<EventModel(id={self.id}, type={self.event_type}, ticket_id={self.ticket_id})>"
