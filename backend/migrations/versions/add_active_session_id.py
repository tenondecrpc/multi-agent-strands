"""Add active_session_id to ticket_states

Revision ID: add_active_session_id
Revises: add_ticket_states_and_events
Create Date: 2026-03-30 19:57:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_active_session_id"
down_revision: Union[str, Sequence[str], None] = "add_ticket_states_and_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticket_states",
        sa.Column("active_session_id", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ticket_states", "active_session_id")
