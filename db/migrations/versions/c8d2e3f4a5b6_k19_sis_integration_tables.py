"""k19 sis integration tables

Revision ID: c8d2e3f4a5b6
Revises: b7a0d74fa430
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b7a0d74fa430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sis_source",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("secret_ref", sa.String(length=255), nullable=True),
        sa.Column("encrypted_secret", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_cursor", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["school_school.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "provider_type", "name", name="uq_sis_source_school_provider_name"),
    )
    op.create_index(op.f("ix_sis_source_school_id"), "sis_source", ["school_id"], unique=False)

    op.create_table(
        "sis_identity_map",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("internal_id", sa.Uuid(), nullable=True),
        sa.Column("external_key", sa.String(length=512), nullable=True),
        sa.Column("payload_hash", sa.String(length=128), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conflict_state", sa.String(length=32), nullable=False),
        sa.Column("conflict_detail", sa.JSON(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["school_school.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sis_source.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "entity_type", "external_id", name="uq_sis_identity_source_entity_external"),
    )
    op.create_index(op.f("ix_sis_identity_map_school_id"), "sis_identity_map", ["school_id"], unique=False)
    op.create_index(op.f("ix_sis_identity_map_source_id"), "sis_identity_map", ["source_id"], unique=False)
    op.create_index(op.f("ix_sis_identity_map_entity_type"), "sis_identity_map", ["entity_type"], unique=False)
    op.create_index(op.f("ix_sis_identity_map_internal_id"), "sis_identity_map", ["internal_id"], unique=False)

    op.create_table(
        "sis_sync_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("triggered_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["school_school.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sis_source.id"]),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["identity_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sis_sync_job_school_id"), "sis_sync_job", ["school_id"], unique=False)
    op.create_index(op.f("ix_sis_sync_job_source_id"), "sis_sync_job", ["source_id"], unique=False)
    op.create_index(op.f("ix_sis_sync_job_triggered_by_user_id"), "sis_sync_job", ["triggered_by_user_id"], unique=False)

    op.create_table(
        "sis_sync_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("internal_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["sis_sync_job.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["school_school.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sis_source.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sis_sync_item_job_id"), "sis_sync_item", ["job_id"], unique=False)
    op.create_index(op.f("ix_sis_sync_item_school_id"), "sis_sync_item", ["school_id"], unique=False)
    op.create_index(op.f("ix_sis_sync_item_source_id"), "sis_sync_item", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sis_sync_item_source_id"), table_name="sis_sync_item")
    op.drop_index(op.f("ix_sis_sync_item_school_id"), table_name="sis_sync_item")
    op.drop_index(op.f("ix_sis_sync_item_job_id"), table_name="sis_sync_item")
    op.drop_table("sis_sync_item")
    op.drop_index(op.f("ix_sis_sync_job_triggered_by_user_id"), table_name="sis_sync_job")
    op.drop_index(op.f("ix_sis_sync_job_source_id"), table_name="sis_sync_job")
    op.drop_index(op.f("ix_sis_sync_job_school_id"), table_name="sis_sync_job")
    op.drop_table("sis_sync_job")
    op.drop_index(op.f("ix_sis_identity_map_internal_id"), table_name="sis_identity_map")
    op.drop_index(op.f("ix_sis_identity_map_entity_type"), table_name="sis_identity_map")
    op.drop_index(op.f("ix_sis_identity_map_source_id"), table_name="sis_identity_map")
    op.drop_index(op.f("ix_sis_identity_map_school_id"), table_name="sis_identity_map")
    op.drop_table("sis_identity_map")
    op.drop_index(op.f("ix_sis_source_school_id"), table_name="sis_source")
    op.drop_table("sis_source")
