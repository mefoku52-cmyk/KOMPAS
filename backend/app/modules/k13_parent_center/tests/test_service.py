import uuid

import pytest

from app.modules.k13_parent_center.services.service import K13Service
from app.shared.identity import GuardianLink, User
from app.shared.school import School
from app.shared.types import Principal, Role, system_principal


def _setup(db_session):
    school_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    child_id = uuid.uuid4()
    other_parent_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(User(id=parent_id, school_id=school_id, username=f"p-{parent_id}", full_name="P", password_hash="x"))
    db_session.add(User(id=child_id, school_id=school_id, username=f"c-{child_id}", full_name="C", password_hash="x"))
    db_session.add(User(id=other_parent_id, school_id=school_id, username=f"o-{other_parent_id}", full_name="O", password_hash="x"))
    db_session.add(GuardianLink(guardian_user_id=parent_id, child_user_id=child_id, school_id=school_id))
    db_session.commit()
    return school_id, parent_id, child_id, other_parent_id


def test_k13_parent_lists_children_and_views_overview(db_session):
    school_id, parent_id, child_id, other_parent_id = _setup(db_session)
    svc = K13Service(db_session)
    parent = Principal(user_id=parent_id, role=Role.PARENT, school_id=school_id)
    children = svc.list_children(parent, school_id=school_id)
    assert str(child_id) in children["child_user_ids"]
    overview = svc.get_child_overview(parent, school_id=school_id, child_user_id=child_id)
    assert overview["child_user_id"] == str(child_id)
    assert "teacher_notes" in overview
    assert overview["teacher_notes"] == []  # no private teacher notes exposed


def test_k13_parent_cannot_view_unlinked_child(db_session):
    school_id, parent_id, child_id, other_parent_id = _setup(db_session)
    svc = K13Service(db_session)
    other_parent = Principal(user_id=other_parent_id, role=Role.PARENT, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.get_child_overview(other_parent, school_id=school_id, child_user_id=child_id)


def test_k13_non_parent_denied(db_session):
    school_id, parent_id, child_id, _ = _setup(db_session)
    svc = K13Service(db_session)
    student = Principal(user_id=uuid.uuid4(), role=Role.STUDENT, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.list_children(student, school_id=school_id)
