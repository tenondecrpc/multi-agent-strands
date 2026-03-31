"""Initial schema: agent sessions, events, ticket states

Revision ID: 282124c5ca1a
Revises:
Create Date: 2026-03-29 18:23:17.223327

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "282124c5ca1a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS sessionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agentsessionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS eventtype CASCADE")
    op.execute("DROP TYPE IF EXISTS eventtype_v2 CASCADE")
    op.execute("DROP TYPE IF EXISTS ticketstage CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_events CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS events CASCADE")
    op.execute("DROP TABLE IF EXISTS ticket_states CASCADE")

    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("ticket_id", sa.String(length=50), nullable=False),
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
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "COMPLETED",
                "FAILED",
                "RETRY",
                name="agentsessionstatus",
            ),
            nullable=False,
        ),
        sa.Column("current_task", sa.String(length=500), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(length=1000), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index(
        op.f("ix_agent_sessions_session_id"),
        "agent_sessions",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_sessions_ticket_id"),
        "agent_sessions",
        ["ticket_id"],
        unique=False,
    )

    op.create_table(
        "agent_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.String(length=100), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "AGENT_STARTED",
                "AGENT_COMPLETED",
                "AGENT_FAILED",
                "TOOL_CALL",
                "STATE_CHANGE",
                "LOG",
                "LLM_CREDIT_EXHAUSTED",
                "LLM_RATE_LIMITED",
                name="eventtype",
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["agent_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_events_session_id", "agent_events", ["session_id"], unique=False
    )

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
        sa.Column("active_session_id", sa.String(length=100), nullable=True),
        sa.Column("context_window", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("artifacts", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("handoff_history", sa.JSON(), server_default="[]", nullable=False),
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
        op.f("ix_ticket_states_ticket_id"), "ticket_states", ["ticket_id"], unique=False
    )
    op.create_index(
        op.f("ix_ticket_states_jira_key"), "ticket_states", ["jira_key"], unique=False
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
                "LLM_CREDIT_EXHAUSTED",
                "LLM_RATE_LIMITED",
                name="eventtype_v2",
            ),
            nullable=False,
        ),
        sa.Column("ticket_id", sa.String(length=50), nullable=False),
        sa.Column("agent_id", sa.String(length=100), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_ticket_id"), "events", ["ticket_id"], unique=False)
    op.create_index(
        op.f("ix_events_event_type"), "events", ["event_type"], unique=False
    )
    op.create_index(op.f("ix_events_timestamp"), "events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_events_timestamp"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index(op.f("ix_events_ticket_id"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_ticket_states_jira_key"), table_name="ticket_states")
    op.drop_index(op.f("ix_ticket_states_ticket_id"), table_name="ticket_states")
    op.drop_table("ticket_states")
    op.drop_index("ix_agent_events_session_id", table_name="agent_events")
    op.drop_table("agent_events")
    op.drop_index(op.f("ix_agent_sessions_session_id"), table_name="agent_sessions")
    op.drop_index(op.f("ix_agent_sessions_ticket_id"), table_name="agent_sessions")
    op.drop_table("agent_sessions")
    op.execute("DROP TYPE IF EXISTS sessionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agentsessionstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS eventtype CASCADE")
    op.execute("DROP TYPE IF EXISTS eventtype_v2 CASCADE")
    op.execute("DROP TYPE IF EXISTS ticketstage CASCADE")
