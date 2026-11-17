"""audit log append-only trigger

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-17 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            "CREATE OR REPLACE FUNCTION audit_log_reject_mutation() "
            "RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'audit_log is append-only'; END; $$ "
            "LANGUAGE plpgsql"
        )
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log")
        op.execute(
            "CREATE TRIGGER audit_log_append_only BEFORE UPDATE OR DELETE ON audit_log "
            "FOR EACH ROW EXECUTE FUNCTION audit_log_reject_mutation()"
        )
    else:
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only_update")
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only_delete")
        op.execute(
            "CREATE TRIGGER audit_log_append_only_update BEFORE UPDATE ON audit_log "
            "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
        )
        op.execute(
            "CREATE TRIGGER audit_log_append_only_delete BEFORE DELETE ON audit_log "
            "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log")
        op.execute("DROP FUNCTION IF EXISTS audit_log_reject_mutation()")
    else:
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only_update")
        op.execute("DROP TRIGGER IF EXISTS audit_log_append_only_delete")
