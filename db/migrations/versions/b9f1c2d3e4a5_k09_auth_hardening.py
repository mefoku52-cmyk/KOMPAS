"""k09 auth hardening

Revision ID: b9f1c2d3e4a5
Revises: 66e26d8f3c95
Create Date: 2026-11-17 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b9f1c2d3e4a5'
down_revision: Union[str, Sequence[str], None] = '66e26d8f3c95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('identity_user') as batch_op:
        batch_op.add_column(sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('identity_revoked_token',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['identity_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_identity_revoked_token_jti'), 'identity_revoked_token', ['jti'], unique=True)
    op.create_index(op.f('ix_identity_revoked_token_user_id'), 'identity_revoked_token', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_identity_revoked_token_user_id'), table_name='identity_revoked_token')
    op.drop_index(op.f('ix_identity_revoked_token_jti'), table_name='identity_revoked_token')
    op.drop_table('identity_revoked_token')
    with op.batch_alter_table('identity_user') as batch_op:
        batch_op.drop_column('password_changed_at')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_count')
