"""k19 sis identity absent runs

Revision ID: d4e5f6a7b8c9
Revises: c8d2e3f4a5b6
Create Date: 2026-11-23 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c8d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sis_identity_map", sa.Column("absent_runs", sa.Integer(), nullable=False, server_default="0"))
    with op.batch_alter_table("sis_identity_map") as batch_op:
        batch_op.alter_column("absent_runs", server_default=None, existing_type=sa.Integer(), existing_nullable=False)


def downgrade() -> None:
    op.drop_column("sis_identity_map", "absent_runs")
