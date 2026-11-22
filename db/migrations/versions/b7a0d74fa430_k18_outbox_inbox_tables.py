"""k18 outbox inbox tables

Revision ID: b7a0d74fa430
Revises: f202ec1baf80
Create Date: 2026-11-22 22:44:37.711182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7a0d74fa430'
down_revision: Union[str, Sequence[str], None] = 'f202ec1baf80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('il_inbox',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('event_id', sa.Uuid(), nullable=False),
    sa.Column('handler', sa.String(length=128), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_inbox_event_id'), 'il_inbox', ['event_id'], unique=False)
    op.create_table('il_outbox',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('event_id', sa.Uuid(), nullable=False),
    sa.Column('event_type', sa.String(length=128), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_outbox_event_id'), 'il_outbox', ['event_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_il_outbox_event_id'), table_name='il_outbox')
    op.drop_table('il_outbox')
    op.drop_index(op.f('ix_il_inbox_event_id'), table_name='il_inbox')
    op.drop_table('il_inbox')
