"""Add ticket_states, agent_sessions, and events tables

Revision ID: add_ticket_states_and_events
Revises: 282124c5ca1a
Create Date: 2026-03-30 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_ticket_states_and_events"
down_revision: Union[str, Sequence[str], None] = "282124c5ca1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new tables for ticket processing pipeline and event bus."""
    op.create_table(
        "ticket_states",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.String(length=50), nullable=False),
        sa.Column("jira_key", sa.String(length=50), nullable=True),
        sa.Column(
            "current_stage",
            sa.Enum(
                "NEW",
                "TRIAGED",
                "IN_ANALYSIS",
                "IN_DEVELOPMENT",
                "IN_REVIEW",
                "IN_TESTING",
                "DONE",
                "BLOCKED",
                name="ticketstage",
            ),
            nullable=False,
        ),
        sa.Column("assigned_agent", sa.String(length=100), nullable=True),
        sa.Column(
            "context_window",
            sa.JSON().with_variant(sa.JSON(), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "artifacts", sa.JSON().with_variant(sa.JSON(), "postgresql"), nullable=False
        ),
        sa.Column(
            "handoff_history",
            sa.JSON().with_variant(sa.JSON(), "postgresql"),
            nullable=False,
        ),
        sa.Column("blocked_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )
    op.create_index(
        "ix_ticket_states_ticket_id", "ticket_states", ["ticket_id"], unique=False
    )
    op.create_index(
        "ix_ticket_states_jira_key", "ticket_states", ["jira_key"], unique=False
    )

    op.execute("DROP TYPE IF EXISTS agentsessionstatus CASCADE")
    op.execute(
        "CREATE TYPE agentsessionstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'RETRY')"
    )
    op.execute("DROP TYPE IF EXISTS agenttype CASCADE")
    op.execute(
        "CREATE TYPE agenttype AS ENUM ('ORCHESTRATOR', 'BACKEND', 'FRONTEND', 'QA', 'ARCHITECT')"
    )

    op.add_column("agent_sessions", sa.Column("session_id", sa.String(length=100), nullable=True))
    op.add_column(
        "agent_sessions",
        sa.Column(
            "agent_type",
            sa.Enum(
                "ORCHESTRATOR",
                "BACKEND",
                "FRONTEND",
                "QA",
                "ARCHITECT",
                name="agenttype",
            ),
            nullable=True,
        ),
    )
    op.add_column("agent_sessions", sa.Column("current_task", sa.String(length=500), nullable=True))
    op.add_column(
        "agent_sessions",
        sa.Column("result", sa.JSON().with_variant(sa.JSON(), "postgresql"), nullable=True),
    )
    op.add_column("agent_sessions", sa.Column("error", sa.String(length=1000), nullable=True))
    op.add_column(
        "agent_sessions",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("agent_sessions", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("agent_sessions", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))

    op.execute("ALTER TABLE agent_sessions ALTER COLUMN status TYPE agentsessionstatus USING status::text::agentsessionstatus")
    op.execute("UPDATE agent_sessions SET started_at = created_at WHERE started_at IS NULL")
    op.alter_column("agent_sessions", "started_at", nullable=False)

    op.create_index(
        "ix_agent_sessions_session_id",
        "agent_sessions",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "TICKET_RECEIVED",
                "TICKET_UPDATED",
                "TICKET_STAGE_CHANGED",
                "AGENT_STARTED",
                "AGENT_COMPLETED",
                "AGENT_FAILED",
                "AGENT_HANDOFF",
                "ARTIFACT_CREATED",
                "COMMENT_ADDED",
                name="eventtype_v2",
            ),
            nullable=False,
        ),
        sa.Column("ticket_id", sa.String(length=50), nullable=False),
        sa.Column("agent_id", sa.String(length=100), nullable=True),
        sa.Column(
            "payload", sa.JSON().with_variant(sa.JSON(), "postgresql"), nullable=False
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_ticket_id", "events", ["ticket_id"], unique=False)
    op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("ix_events_timestamp", "events", ["timestamp"], unique=False)


def downgrade() -> None:
    """Remove new tables and columns."""
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_ticket_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_agent_sessions_session_id", table_name="agent_sessions")
    op.drop_column("agent_sessions", "retry_count")
    op.drop_column("agent_sessions", "completed_at")
    op.drop_column("agent_sessions", "started_at")
    op.drop_column("agent_sessions", "error")
    op.drop_column("agent_sessions", "result")
    op.drop_column("agent_sessions", "current_task")
    op.drop_column("agent_sessions", "agent_type")
    op.drop_column("agent_sessions", "session_id")

    op.execute("ALTER TABLE agent_sessions ALTER COLUMN status TYPE sessionstatus USING status::text::sessionstatus")
    op.execute("DROP TYPE IF EXISTS agentsessionstatus")
    op.execute("DROP TYPE IF EXISTS agenttype")

    op.drop_index("ix_ticket_states_jira_key", table_name="ticket_states")
    op.drop_index("ix_ticket_states_ticket_id", table_name="ticket_states")
    op.drop_table("ticket_states")
