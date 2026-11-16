# Dátový model

Generované z SQLAlchemy metadata (zdroj pravdy schémy). Tabuľky sú podľa prefixov oblastí (D3).

## Oblasť: identity
- `identity_guardian_link` (id:CHAR(32), guardian_user_id:CHAR(32), child_user_id:CHAR(32), school_id:CHAR(32), relationship:VARCHAR(64), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `identity_role_assignment` (id:CHAR(32), user_id:CHAR(32), school_id:CHAR(32), role:VARCHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `identity_user` (id:CHAR(32), school_id:CHAR(32), username:VARCHAR(150), full_name:VARCHAR(255), password_hash:VARCHAR(512), is_active:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: school
- `school_class_group` (id:CHAR(32), school_id:CHAR(32), school_year_id:CHAR(32), name:VARCHAR(64), grade:INTEGER, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `school_class_teacher` (id:CHAR(32), school_id:CHAR(32), class_group_id:CHAR(32), teacher_user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `school_enrollment` (id:CHAR(32), school_id:CHAR(32), school_year_id:CHAR(32), class_group_id:CHAR(32), student_user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `school_school` (id:CHAR(32), name:VARCHAR(255), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `school_year` (id:CHAR(32), school_id:CHAR(32), name:VARCHAR(64), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: curriculum
- `curriculum_subject` (id:CHAR(32), school_id:CHAR(32), name:VARCHAR(255), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `curriculum_subject_workspace` (id:CHAR(32), school_id:CHAR(32), subject_id:CHAR(32), teacher_user_id:CHAR(32), name:VARCHAR(255), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `curriculum_topic` (id:CHAR(32), school_id:CHAR(32), subject_id:CHAR(32), parent_topic_id:CHAR(32), name:VARCHAR(255), grade:INTEGER, order_index:INTEGER, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `curriculum_workspace_topic_node` (id:CHAR(32), school_id:CHAR(32), workspace_id:CHAR(32), topic_id:CHAR(32), parent_node_id:CHAR(32), title:VARCHAR(255), order_index:INTEGER, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: learning
- `learning_attempt` (id:CHAR(32), school_id:CHAR(32), task_id:CHAR(32), student_user_id:CHAR(32), answer:TEXT, is_correct:BOOLEAN, evaluated:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `learning_mission` (id:CHAR(32), school_id:CHAR(32), topic_id:CHAR(32), title:VARCHAR(255), is_verification:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `learning_simulation_definition` (id:CHAR(32), school_id:CHAR(32), key:VARCHAR(128), name:VARCHAR(255), description:TEXT, param_schema:TEXT, compute_key:VARCHAR(128), is_active:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `learning_simulation_run` (id:CHAR(32), school_id:CHAR(32), definition_id:CHAR(32), user_id:CHAR(32), inputs:TEXT, outputs:TEXT, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `learning_task` (id:CHAR(32), school_id:CHAR(32), mission_id:CHAR(32), task_type:VARCHAR(10), prompt:TEXT, expected_answer:TEXT, order_index:INTEGER, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: progress
- `progress_adaptive_recommendation` (id:CHAR(32), school_id:CHAR(32), student_user_id:CHAR(32), topic_id:CHAR(32), reason:TEXT, suggested_action:VARCHAR(64), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `progress_analytics_snapshot` (id:CHAR(32), school_id:CHAR(32), metric_key:VARCHAR(128), group_key:VARCHAR(255), group_size:INTEGER, suppressed:INTEGER, value_count:INTEGER, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `progress_student_profile` (id:CHAR(32), school_id:CHAR(32), student_user_id:CHAR(32), school_year_id:CHAR(32), grade:INTEGER, label:VARCHAR(255), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `progress_topic_state` (id:CHAR(32), school_id:CHAR(32), student_user_id:CHAR(32), topic_id:CHAR(32), kind:VARCHAR(9), status:VARCHAR(20), evidence_attempt_ref:VARCHAR(255), is_verification_evidence:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: teacher_workspace
- `teacher_workspace_assistant_draft` (id:CHAR(32), school_id:CHAR(32), teacher_user_id:CHAR(32), title:VARCHAR(255), draft_type:VARCHAR(32), content:TEXT, status:VARCHAR(22), source_refs:TEXT, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `teacher_workspace_library_item` (id:CHAR(32), school_id:CHAR(32), owner_teacher_user_id:CHAR(32), title:VARCHAR(255), description:TEXT, archived:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `teacher_workspace_library_tag` (id:CHAR(32), school_id:CHAR(32), item_id:CHAR(32), tag:VARCHAR(64), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `teacher_workspace_library_version` (id:CHAR(32), school_id:CHAR(32), item_id:CHAR(32), version_number:INTEGER, storage_key:VARCHAR(512), content_text:TEXT, note:VARCHAR(255), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: organization
- `organization_assignment` (id:CHAR(32), school_id:CHAR(32), task_id:CHAR(32), assignee_user_id:CHAR(32), role_in_task:VARCHAR(64), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_operation_request` (id:CHAR(32), school_id:CHAR(32), requester_user_id:CHAR(32), request_type:VARCHAR(32), title:VARCHAR(255), description:TEXT, status:VARCHAR(11), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_plan` (id:CHAR(32), school_id:CHAR(32), name:VARCHAR(255), description:TEXT, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_project` (id:CHAR(32), school_id:CHAR(32), title:VARCHAR(255), description:TEXT, status:VARCHAR(32), owner_user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_project_member` (id:CHAR(32), school_id:CHAR(32), project_id:CHAR(32), user_id:CHAR(32), role:VARCHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_project_submission` (id:CHAR(32), school_id:CHAR(32), task_id:CHAR(32), submitted_by_user_id:CHAR(32), content:TEXT, status:VARCHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_project_task` (id:CHAR(32), school_id:CHAR(32), project_id:CHAR(32), title:VARCHAR(255), description:TEXT, status:VARCHAR(32), assignee_user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `organization_task` (id:CHAR(32), school_id:CHAR(32), title:VARCHAR(255), description:TEXT, status:VARCHAR(32), due_at:DATETIME, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: communication
- `communication_message` (id:CHAR(32), school_id:CHAR(32), thread_id:CHAR(32), sender_user_id:CHAR(32), body:TEXT, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `communication_thread` (id:CHAR(32), school_id:CHAR(32), subject:VARCHAR(255), is_private:BOOLEAN, created_by_user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `communication_thread_participant` (id:CHAR(32), school_id:CHAR(32), thread_id:CHAR(32), user_id:CHAR(32), valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: ai_knowledge
- `ai_knowledge_context_memory` (id:CHAR(32), school_id:CHAR(32), source_record_ref:VARCHAR(255), content:TEXT, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)
- `ai_knowledge_source` (id:CHAR(32), school_id:CHAR(32), name:VARCHAR(255), source_type:VARCHAR(64), content:TEXT, approved:BOOLEAN, valid_from:DATETIME, valid_to:DATETIME, version:INTEGER, is_demo:BOOLEAN)

## Oblasť: audit
- `audit_event_log` (id:CHAR(32), event_type:VARCHAR(128), school_id:CHAR(32), payload:TEXT, occurred_at:DATETIME)
- `audit_log` (id:CHAR(32), timestamp:DATETIME, principal_id:CHAR(32), principal_role:VARCHAR(32), school_id:CHAR(32), action:VARCHAR(128), resource:VARCHAR(255), purpose:VARCHAR(255), outcome:VARCHAR(32), details:TEXT, prev_hash:VARCHAR(64), record_hash:VARCHAR(64))
