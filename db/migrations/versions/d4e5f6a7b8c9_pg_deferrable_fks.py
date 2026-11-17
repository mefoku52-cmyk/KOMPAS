"""pg deferrable foreign keys

Revision ID: d4e5f6a7b8c9
Revises: b9f1c2d3e4a5
Create Date: 2026-11-17 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'b9f1c2d3e4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _foreign_keys():
    return op.get_bind().execute(sa.text(
        "SELECT c.conname, c.conrelid::regclass::text AS table_name "
        "FROM pg_constraint c "
        "JOIN pg_namespace n ON n.oid = c.connamespace "
        "WHERE c.contype = 'f' AND n.nspname = current_schema()"
    )).all()


def upgrade() -> None:
    if op.get_bind().dialect.name != 'postgresql':
        return
    for name, table_name in _foreign_keys():
        op.execute(f'ALTER TABLE {table_name} ALTER CONSTRAINT "{name}" DEFERRABLE INITIALLY DEFERRED')


def downgrade() -> None:
    if op.get_bind().dialect.name != 'postgresql':
        return
    for name, table_name in _foreign_keys():
        op.execute(f'ALTER TABLE {table_name} ALTER CONSTRAINT "{name}" NOT DEFERRABLE')
