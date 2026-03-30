"""Consolidate agent_sessions tables

Revision ID: consolidate_agent_sessions
Revises: add_ticket_states_and_events
Create Date: 2026-03-30

"""

from alembic import op
import sqlalchemy as sa


revision = "consolidate_agent_sessions"
down_revision = "add_ticket_states_and_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_sessions CASCADE")
    op.execute("ALTER TABLE agent_sessions_v2 RENAME TO agent_sessions")


def downgrade() -> None:
    op.execute("ALTER TABLE agent_sessions RENAME TO agent_sessions_v2")
