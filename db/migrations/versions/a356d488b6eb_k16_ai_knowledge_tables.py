"""k16 ai knowledge tables

Revision ID: a356d488b6eb
Revises: 822ee05ee37a
Create Date: 2026-11-16 15:23:54.416001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a356d488b6eb'
down_revision: Union[str, Sequence[str], None] = '822ee05ee37a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_knowledge_source',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_knowledge_source_school_id'), 'ai_knowledge_source', ['school_id'], unique=False)

    op.create_table(
        'ai_knowledge_context_memory',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('source_record_ref', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_knowledge_context_memory_school_id'), 'ai_knowledge_context_memory', ['school_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_knowledge_context_memory_school_id'), table_name='ai_knowledge_context_memory')
    op.drop_table('ai_knowledge_context_memory')
    op.drop_index(op.f('ix_ai_knowledge_source_school_id'), table_name='ai_knowledge_source')
    op.drop_table('ai_knowledge_source')
