"""k18 intelligence layer tables

Revision ID: f202ec1baf80
Revises: 818426796485
Create Date: 2026-11-22 22:37:35.888627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f202ec1baf80'
down_revision: Union[str, Sequence[str], None] = '818426796485'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('il_audit',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actor', sa.String(length=128), nullable=False),
    sa.Column('action', sa.String(length=128), nullable=False),
    sa.Column('entity_type', sa.String(length=64), nullable=True),
    sa.Column('entity_id', sa.String(length=128), nullable=True),
    sa.Column('details', sa.JSON(), nullable=False),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_audit_action'), 'il_audit', ['action'], unique=False)
    op.create_index(op.f('ix_il_audit_school_id'), 'il_audit', ['school_id'], unique=False)
    op.create_table('il_communication',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('initiative_id', sa.Uuid(), nullable=False),
    sa.Column('channel', sa.String(length=32), nullable=False),
    sa.Column('content_key', sa.String(length=128), nullable=False),
    sa.Column('locale', sa.String(length=8), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_communication_initiative_id'), 'il_communication', ['initiative_id'], unique=False)
    op.create_index(op.f('ix_il_communication_school_id'), 'il_communication', ['school_id'], unique=False)
    op.create_table('il_context_memory',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_type', sa.String(length=64), nullable=False),
    sa.Column('entity_id', sa.String(length=128), nullable=False),
    sa.Column('context_type', sa.String(length=64), nullable=False),
    sa.Column('context', sa.JSON(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
    sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_event_id', sa.Uuid(), nullable=True),
    sa.Column('source_record_ref', sa.String(length=255), nullable=True),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_context_memory_entity_id'), 'il_context_memory', ['entity_id'], unique=False)
    op.create_index(op.f('ix_il_context_memory_entity_type'), 'il_context_memory', ['entity_type'], unique=False)
    op.create_index(op.f('ix_il_context_memory_school_id'), 'il_context_memory', ['school_id'], unique=False)
    op.create_index(op.f('ix_il_context_memory_source_event_id'), 'il_context_memory', ['source_event_id'], unique=False)
    op.create_table('il_dead_letter',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('event_id', sa.Uuid(), nullable=False),
    sa.Column('handler', sa.String(length=128), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('error', sa.Text(), nullable=False),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_dead_letter_event_id'), 'il_dead_letter', ['event_id'], unique=False)
    op.create_index(op.f('ix_il_dead_letter_school_id'), 'il_dead_letter', ['school_id'], unique=False)
    op.create_table('il_hypothesis',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('situation_id', sa.Uuid(), nullable=True),
    sa.Column('entity_type', sa.String(length=64), nullable=False),
    sa.Column('entity_id', sa.String(length=128), nullable=False),
    sa.Column('hypothesis_text', sa.Text(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('evidence', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_hypothesis_entity_id'), 'il_hypothesis', ['entity_id'], unique=False)
    op.create_index(op.f('ix_il_hypothesis_school_id'), 'il_hypothesis', ['school_id'], unique=False)
    op.create_index(op.f('ix_il_hypothesis_situation_id'), 'il_hypothesis', ['situation_id'], unique=False)
    op.create_table('il_initiative',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('situation_id', sa.Uuid(), nullable=True),
    sa.Column('entity_type', sa.String(length=64), nullable=False),
    sa.Column('entity_id', sa.String(length=128), nullable=False),
    sa.Column('action_type', sa.String(length=64), nullable=False),
    sa.Column('decision', sa.String(length=32), nullable=False),
    sa.Column('recipient_user_id', sa.Uuid(), nullable=True),
    sa.Column('recipient_role', sa.String(length=32), nullable=True),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('urgency', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decided_by', sa.String(length=128), nullable=True),
    sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_initiative_entity_id'), 'il_initiative', ['entity_id'], unique=False)
    op.create_index(op.f('ix_il_initiative_recipient_user_id'), 'il_initiative', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_il_initiative_school_id'), 'il_initiative', ['school_id'], unique=False)
    op.create_index(op.f('ix_il_initiative_situation_id'), 'il_initiative', ['situation_id'], unique=False)
    op.create_table('il_outcome',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('initiative_id', sa.Uuid(), nullable=False),
    sa.Column('outcome', sa.String(length=32), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.Column('feedback_source', sa.String(length=32), nullable=True),
    sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_outcome_initiative_id'), 'il_outcome', ['initiative_id'], unique=False)
    op.create_index(op.f('ix_il_outcome_school_id'), 'il_outcome', ['school_id'], unique=False)
    op.create_table('il_perception_event',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('event_id', sa.Uuid(), nullable=False),
    sa.Column('event_type', sa.String(length=128), nullable=False),
    sa.Column('source', sa.String(length=64), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processing_status', sa.String(length=32), nullable=False),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.Column('correlation_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_perception_event_event_id'), 'il_perception_event', ['event_id'], unique=True)
    op.create_index(op.f('ix_il_perception_event_school_id'), 'il_perception_event', ['school_id'], unique=False)
    op.create_table('il_prediction',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('hypothesis_id', sa.Uuid(), nullable=True),
    sa.Column('entity_id', sa.String(length=128), nullable=False),
    sa.Column('prediction_text', sa.Text(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('uncertainty', sa.String(length=16), nullable=False),
    sa.Column('alternatives', sa.JSON(), nullable=False),
    sa.Column('outcome', sa.String(length=32), nullable=True),
    sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('school_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_il_prediction_entity_id'), 'il_prediction', ['entity_id'], unique=False)
    op.create_index(op.f('ix_il_prediction_hypothesis_id'), 'il_prediction', ['hypothesis_id'], unique=False)
    op.create_index(op.f('ix_il_prediction_school_id'), 'il_prediction', ['school_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_il_prediction_entity_id'), table_name='il_prediction')
    op.drop_index(op.f('ix_il_prediction_hypothesis_id'), table_name='il_prediction')
    op.drop_index(op.f('ix_il_prediction_school_id'), table_name='il_prediction')
    op.drop_table('il_prediction')
    op.drop_index(op.f('ix_il_perception_event_event_id'), table_name='il_perception_event')
    op.drop_index(op.f('ix_il_perception_event_school_id'), table_name='il_perception_event')
    op.drop_table('il_perception_event')
    op.drop_index(op.f('ix_il_outcome_initiative_id'), table_name='il_outcome')
    op.drop_index(op.f('ix_il_outcome_school_id'), table_name='il_outcome')
    op.drop_table('il_outcome')
    op.drop_index(op.f('ix_il_initiative_entity_id'), table_name='il_initiative')
    op.drop_index(op.f('ix_il_initiative_recipient_user_id'), table_name='il_initiative')
    op.drop_index(op.f('ix_il_initiative_school_id'), table_name='il_initiative')
    op.drop_index(op.f('ix_il_initiative_situation_id'), table_name='il_initiative')
    op.drop_table('il_initiative')
    op.drop_index(op.f('ix_il_hypothesis_entity_id'), table_name='il_hypothesis')
    op.drop_index(op.f('ix_il_hypothesis_school_id'), table_name='il_hypothesis')
    op.drop_index(op.f('ix_il_hypothesis_situation_id'), table_name='il_hypothesis')
    op.drop_table('il_hypothesis')
    op.drop_index(op.f('ix_il_dead_letter_event_id'), table_name='il_dead_letter')
    op.drop_index(op.f('ix_il_dead_letter_school_id'), table_name='il_dead_letter')
    op.drop_table('il_dead_letter')
    op.drop_index(op.f('ix_il_context_memory_entity_id'), table_name='il_context_memory')
    op.drop_index(op.f('ix_il_context_memory_entity_type'), table_name='il_context_memory')
    op.drop_index(op.f('ix_il_context_memory_school_id'), table_name='il_context_memory')
    op.drop_index(op.f('ix_il_context_memory_source_event_id'), table_name='il_context_memory')
    op.drop_table('il_context_memory')
    op.drop_index(op.f('ix_il_communication_initiative_id'), table_name='il_communication')
    op.drop_index(op.f('ix_il_communication_school_id'), table_name='il_communication')
    op.drop_table('il_communication')
    op.drop_index(op.f('ix_il_audit_action'), table_name='il_audit')
    op.drop_index(op.f('ix_il_audit_school_id'), table_name='il_audit')
    op.drop_table('il_audit')
