import uuid

import pytest

from app.core.permissions.policy import Scope, Visibility, authorize
from app.shared.identity import GuardianLink, User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear
from app.modules.k09_class_overview.domain.models import ClassTeacherAssignment
from app.shared.types import Principal, Role


def _setup(db_session):
    school_id = uuid.uuid4()
    year_id = uuid.uuid4()
    class_a = uuid.uuid4()
    class_b = uuid.uuid4()
    student_a = uuid.uuid4()
    student_b = uuid.uuid4()
    parent_a = uuid.uuid4()
    teacher_a = uuid.uuid4()
    teacher_b = uuid.uuid4()
    leader = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.flush()
    db_session.add(SchoolYear(id=year_id, school_id=school_id, name="2026/27"))
    db_session.add(ClassGroup(id=class_a, school_id=school_id, school_year_id=year_id, name="5A", grade=5))
    db_session.add(ClassGroup(id=class_b, school_id=school_id, school_year_id=year_id, name="5B", grade=5))
    db_session.flush()
    for uid, n in [(student_a, "sa"), (student_b, "sb"), (parent_a, "pa"), (teacher_a, "ta"), (teacher_b, "tb"), (leader, "l")]:
        db_session.add(User(id=uid, school_id=school_id, username=f"{n}-{uid}", full_name=n, password_hash="x"))
    db_session.flush()
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_a, student_user_id=student_a))
    db_session.add(Enrollment(school_id=school_id, school_year_id=year_id, class_group_id=class_b, student_user_id=student_b))
    db_session.flush()
    db_session.add(GuardianLink(guardian_user_id=parent_a, child_user_id=student_a, school_id=school_id))
    db_session.add(ClassTeacherAssignment(school_id=school_id, class_group_id=class_a, teacher_user_id=teacher_a))
    db_session.commit()
    return {
        "school_id": school_id,
        "class_a": class_a,
        "class_b": class_b,
        "student_a": student_a,
        "student_b": student_b,
        "parent_a": parent_a,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "leader": leader,
    }


@pytest.mark.parametrize(
    "role_key, action, ctx_builder, expected, reason_contains",
    [
        ("student_a", "read_progress", lambda c: {"scope": Scope.SELF, "owner_user_id": c["student_a"], "student_user_id": c["student_a"]}, True, None),
        ("student_a", "read_progress", lambda c: {"scope": Scope.SELF, "owner_user_id": c["student_b"], "student_user_id": c["student_b"]}, False, "not_self"),
        ("parent_a", "read_child", lambda c: {"scope": Scope.GUARDIAN_OF, "student_user_id": c["student_a"], "child_user_id": c["student_a"]}, True, None),
        ("parent_a", "read_child", lambda c: {"scope": Scope.GUARDIAN_OF, "student_user_id": c["student_b"], "child_user_id": c["student_b"]}, False, "not_guardian_of"),
        ("teacher_a", "read_class_student", lambda c: {"scope": Scope.TEACHES_CLASS, "student_user_id": c["student_a"], "class_group_id": c["class_a"], "teacher_user_id": c["teacher_a"], "teaches": True}, True, None),
        ("teacher_a", "read_class_student", lambda c: {"scope": Scope.TEACHES_CLASS, "student_user_id": c["student_b"], "class_group_id": c["class_b"], "teacher_user_id": c["teacher_b"], "teaches": False}, False, "teacher_not_assigned_to_class"),
        ("leader", "read_aggregate", lambda c: {"scope": Scope.SCHOOL_AGGREGATE, "school_id": c["school_id"]}, True, None),
        ("leader", "read_individual", lambda c: {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE, "school_id": c["school_id"], "student_user_id": c["student_a"], "purpose": "support"}, True, None),
        ("leader", "read_individual", lambda c: {"scope": Scope.SCHOOL_INDIVIDUAL_WITH_PURPOSE, "school_id": c["school_id"], "student_user_id": c["student_a"], "purpose": ""}, False, "purpose_required"),
        ("teacher_a", "read_note", lambda c: {"visibility": Visibility.TEACHER_PRIVATE_NOTE, "owner_user_id": c["teacher_a"]}, True, None),
        ("parent_a", "read_note", lambda c: {"visibility": Visibility.TEACHER_PRIVATE_NOTE, "owner_user_id": c["teacher_a"]}, False, "teacher_private_note_restricted"),
        ("student_a", "read_note", lambda c: {"visibility": Visibility.TEACHER_PRIVATE_NOTE, "owner_user_id": c["teacher_a"]}, False, "teacher_private_note_restricted"),
        ("parent_a", "read_comm", lambda c: {"visibility": Visibility.PARENT_PRIVATE_COMMUNICATION, "participants": [c["parent_a"], c["teacher_a"]]}, True, None),
        ("teacher_a", "read_comm", lambda c: {"visibility": Visibility.PARENT_PRIVATE_COMMUNICATION, "participants": [c["parent_a"], c["teacher_b"]]}, False, "parent_private_communication_restricted"),
        ("student_a", "read_aggregate", lambda c: {"scope": Scope.SCHOOL_AGGREGATE, "school_id": c["school_id"]}, False, "school_aggregate_denied"),
        ("parent_a", "read_class", lambda c: {"scope": Scope.TEACHES_CLASS, "student_user_id": c["student_a"], "class_group_id": c["class_a"], "teacher_user_id": c["parent_a"], "teaches": False}, False, "not_teacher"),
        ("student_a", "read_any", lambda c: {}, False, "deny_by_default"),
    ],
)
def test_permissions_matrix(db_session, role_key, action, ctx_builder, expected, reason_contains):
    ctx = _setup(db_session)
    principals = {
        "student_a": Principal(user_id=ctx["student_a"], role=Role.STUDENT, school_id=ctx["school_id"]),
        "student_b": Principal(user_id=ctx["student_b"], role=Role.STUDENT, school_id=ctx["school_id"]),
        "parent_a": Principal(user_id=ctx["parent_a"], role=Role.PARENT, school_id=ctx["school_id"]),
        "teacher_a": Principal(user_id=ctx["teacher_a"], role=Role.TEACHER, school_id=ctx["school_id"]),
        "teacher_b": Principal(user_id=ctx["teacher_b"], role=Role.TEACHER, school_id=ctx["school_id"]),
        "leader": Principal(user_id=ctx["leader"], role=Role.LEADERSHIP, school_id=ctx["school_id"]),
    }
    principal = principals[role_key]
    context = ctx_builder(ctx)
    decision = authorize(principal, action, "resource", context=context, db=db_session)
    assert decision.allowed is expected
    if reason_contains:
        assert reason_contains in decision.reason
