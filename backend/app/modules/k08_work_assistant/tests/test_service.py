import uuid

import pytest

from app.modules.k08_work_assistant.domain.models import DraftStatus
from app.modules.k08_work_assistant.services.service import K08Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role, system_principal


def _sys(school_id):
    p = system_principal()
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def _setup(db_session):
    school_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    other_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=other_id, school_id=school_id, username=f"o-{other_id}", full_name="O", password_hash="x"))
    db_session.commit()
    return school_id, teacher_id, other_id


def test_k08_generate_template_draft_and_approval_flow(db_session):
    school_id, teacher_id, _ = _setup(db_session)
    svc = K08Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    draft = svc.generate_draft(teacher, school_id=school_id, teacher_user_id=teacher_id, title="Pracovny list", draft_type="worksheet", topics=["Zlomky"], use_orchestrator=False)
    assert draft.status == DraftStatus.DRAFT.value
    assert "vyzaduje schvalenie ucitelom" in draft.content
    draft = svc.submit_for_approval(teacher, draft.id)
    assert draft.status == DraftStatus.SUBMITTED_FOR_APPROVAL.value
    draft = svc.approve(teacher, draft.id)
    assert draft.status == DraftStatus.APPROVED.value


def test_k08_cannot_approve_without_submission(db_session):
    school_id, teacher_id, _ = _setup(db_session)
    svc = K08Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    draft = svc.generate_draft(teacher, school_id=school_id, teacher_user_id=teacher_id, title="Test", draft_type="test", topics=[], use_orchestrator=False)
    with pytest.raises(ValueError):
        svc.approve(teacher, draft.id)


def test_k08_other_teacher_denied(db_session):
    school_id, teacher_id, other_id = _setup(db_session)
    svc = K08Service(db_session)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    draft = svc.generate_draft(teacher, school_id=school_id, teacher_user_id=teacher_id, title="Test", draft_type="test")
    db_session.commit()
    other = Principal(user_id=other_id, role=Role.TEACHER, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.list_drafts(other, school_id=school_id, teacher_user_id=teacher_id)
    with pytest.raises(PermissionError):
        svc.submit_for_approval(other, draft.id)
