"""query indexes and integrity checks

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-17 03:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = (
    ('ix_identity_user_username', 'identity_user', ['username']),
    ('ix_audit_log_school_timestamp', 'audit_log', ['school_id', 'timestamp']),
    ('ix_audit_log_timestamp_id', 'audit_log', ['timestamp', 'id']),
    ('ix_school_enrollment_school_year_class', 'school_enrollment', ['school_id', 'school_year_id', 'class_group_id']),
    ('ix_school_enrollment_school_class_student', 'school_enrollment', ['school_id', 'class_group_id', 'student_user_id']),
    ('ix_progress_topic_state_school_student_topic_valid', 'progress_topic_state', ['school_id', 'student_user_id', 'topic_id', 'valid_from']),
    ('ix_progress_student_profile_student_valid_version', 'progress_student_profile', ['student_user_id', 'valid_from', 'version']),
    ('ix_learning_attempt_student_valid', 'learning_attempt', ['student_user_id', 'valid_from']),
    ('ix_progress_adaptive_recommendation_student_valid', 'progress_adaptive_recommendation', ['student_user_id', 'valid_from']),
    ('ix_curriculum_workspace_topic_node_workspace_parent_order', 'curriculum_workspace_topic_node', ['workspace_id', 'parent_node_id', 'order_index']),
    ('ix_learning_task_mission_order', 'learning_task', ['mission_id', 'order_index']),
    ('ix_communication_message_thread_valid', 'communication_message', ['thread_id', 'valid_from']),
    ('ix_ai_knowledge_source_approved_school', 'ai_knowledge_source', ['approved', 'school_id']),
    ('ix_teacher_workspace_library_item_school_owner_archived', 'teacher_workspace_library_item', ['school_id', 'owner_teacher_user_id', 'archived']),
    ('ix_teacher_workspace_assistant_draft_school_teacher', 'teacher_workspace_assistant_draft', ['school_id', 'teacher_user_id']),
)


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns, unique=False)
    with op.batch_alter_table('identity_user') as batch:
        batch.create_check_constraint(
            'ck_identity_user_failed_login_count_nonnegative',
            'failed_login_count >= 0',
        )
    with op.batch_alter_table('identity_role_assignment') as batch:
        batch.create_check_constraint(
            'ck_identity_role_assignment_role',
            "role IN ('student', 'teacher', 'leadership', 'parent')",
        )


def downgrade() -> None:
    with op.batch_alter_table('identity_role_assignment') as batch:
        batch.drop_constraint('ck_identity_role_assignment_role', type_='check')
    with op.batch_alter_table('identity_user') as batch:
        batch.drop_constraint('ck_identity_user_failed_login_count_nonnegative', type_='check')
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)
