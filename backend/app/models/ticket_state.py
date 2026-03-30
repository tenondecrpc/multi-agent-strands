import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TicketStage(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    IN_ANALYSIS = "IN_ANALYSIS"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    IN_REVIEW = "IN_REVIEW"
    IN_TESTING = "IN_TESTING"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


VALID_TRANSITIONS = {
    TicketStage.NEW: {TicketStage.TRIAGED, TicketStage.BLOCKED},
    TicketStage.TRIAGED: {
        TicketStage.IN_ANALYSIS,
        TicketStage.IN_DEVELOPMENT,
        TicketStage.BLOCKED,
    },
    TicketStage.IN_ANALYSIS: {TicketStage.IN_DEVELOPMENT, TicketStage.BLOCKED},
    TicketStage.IN_DEVELOPMENT: {TicketStage.IN_REVIEW, TicketStage.BLOCKED},
    TicketStage.IN_REVIEW: {
        TicketStage.IN_TESTING,
        TicketStage.IN_DEVELOPMENT,
        TicketStage.BLOCKED,
    },
    TicketStage.IN_TESTING: {
        TicketStage.DONE,
        TicketStage.IN_REVIEW,
        TicketStage.BLOCKED,
    },
    TicketStage.BLOCKED: {
        TicketStage.NEW,
        TicketStage.TRIAGED,
        TicketStage.IN_ANALYSIS,
        TicketStage.IN_DEVELOPMENT,
        TicketStage.IN_REVIEW,
        TicketStage.IN_TESTING,
    },
    TicketStage.DONE: set(),
}


class TicketState(Base):
    __tablename__ = "ticket_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    jira_key: Mapped[str] = mapped_column(String(50), nullable=True)
    current_stage: Mapped[TicketStage] = mapped_column(
        nullable=False, default=TicketStage.NEW
    )
    assigned_agent: Mapped[str] = mapped_column(String(100), nullable=True)
    context_window: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    artifacts: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    handoff_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    blocked_reason: Mapped[str] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ticket_states_ticket_id", "ticket_id"),
        Index("ix_ticket_states_jira_key", "jira_key"),
    )

    def can_transition_to(self, new_stage: TicketStage) -> bool:
        if self.current_stage == TicketStage.BLOCKED:
            return True
        return new_stage in VALID_TRANSITIONS.get(self.current_stage, set())

    def __repr__(self) -> str:
        return f"<TicketState(ticket_id={self.ticket_id}, stage={self.current_stage})>"
