"""Create K17 wellbeing observations table.

Revision ID: 818426796485
Revises: f6a7b8c9d0e1
Create Date: 2026-11-21 11:31:18.396865
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "818426796485"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    state = sa.Enum("NEUTRAL", "COGNITIVE_OVERLOAD", "AVOIDANCE", "FLOW", name="behavioralstate")
    op.create_table(
        "k17_wellbeing_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("inferred_state", state, nullable=False),
        sa.Column("alert_level", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_k17_wellbeing_observations_student_id", "k17_wellbeing_observations", ["student_id"])
    op.create_index("ix_k17_wellbeing_observations_session_id", "k17_wellbeing_observations", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_k17_wellbeing_observations_session_id", table_name="k17_wellbeing_observations")
    op.drop_index("ix_k17_wellbeing_observations_student_id", table_name="k17_wellbeing_observations")
    op.drop_table("k17_wellbeing_observations")
