"""Enforce unique K18 outbox/inbox event keys.

Revision ID: e9a8b7c6d5f4
Revises: d4e6f7a8b9c0
"""
from alembic import op

revision = "e9a8b7c6d5f4"
down_revision = "d4e6f7a8b9c0"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index("uq_il_outbox_event_id", "il_outbox", ["event_id"], unique=True)
    op.create_index("uq_il_inbox_event_handler", "il_inbox", ["event_id", "handler"], unique=True)

def downgrade() -> None:
    op.drop_index("uq_il_inbox_event_handler", table_name="il_inbox")
    op.drop_index("uq_il_outbox_event_id", table_name="il_outbox")
