import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, Index, String, func, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.agent_event import AgentEvent


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    BACKEND = "backend"
    FRONTEND = "frontend"
    QA = "qa"
    ARCHITECT = "architect"


class AgentSessionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    ticket_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType), nullable=False)
    status: Mapped[AgentSessionStatus] = mapped_column(
        SQLEnum(AgentSessionStatus), default=AgentSessionStatus.PENDING, nullable=False
    )
    current_task: Mapped[str] = mapped_column(String(500), nullable=True)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    events: Mapped[list["AgentEvent"]] = relationship(
        "AgentEvent", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_sessions_session_id", "session_id"),
        Index("ix_agent_sessions_ticket_id", "ticket_id"),
    )

    def mark_running(self) -> None:
        self.status = AgentSessionStatus.RUNNING

    def mark_completed(self, result: dict[str, Any]) -> None:
        self.status = AgentSessionStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = AgentSessionStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    def mark_retry(self) -> None:
        self.status = AgentSessionStatus.RETRY
        self.retry_count += 1

    def __repr__(self) -> str:
        return f"<AgentSession(session_id={self.session_id}, ticket_id={self.ticket_id}, status={self.status})>"
