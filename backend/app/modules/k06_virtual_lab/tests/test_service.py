import uuid

import pytest

from app.modules.k06_virtual_lab.services.service import K06Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role


def _setup(db_session):
    school_id = uuid.uuid4()
    user_id = uuid.uuid4()
    other_school = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(School(id=other_school, name=f"S-{other_school}"))
    db_session.add(User(id=user_id, school_id=school_id, username=f"u-{user_id}", full_name="U", password_hash="x"))
    db_session.commit()
    return school_id, user_id, other_school


def test_k06_lists_sample_and_runs_deterministic_compute(db_session):
    school_id, user_id, _ = _setup(db_session)
    svc = K06Service(db_session)
    user = Principal(user_id=user_id, role=Role.STUDENT, school_id=school_id)
    defs = svc.list_definitions(user, school_id=school_id)
    assert any(d.key == "sample.ohms_law" for d in defs)
    sample = [d for d in defs if d.key == "sample.ohms_law"][0]
    run, outputs = svc.run_simulation(user, school_id=school_id, definition_id=sample.id, inputs={"voltage": 10, "resistance": 2})
    db_session.commit()
    assert outputs["current"] == 5.0
    assert run.outputs


def test_k06_wrong_school_denied(db_session):
    school_id, user_id, other_school = _setup(db_session)
    svc = K06Service(db_session)
    user = Principal(user_id=user_id, role=Role.STUDENT, school_id=school_id)
    svc.ensure_sample_definition()
    sample = svc.repo.get_definition_by_key("sample.ohms_law")
    with pytest.raises(PermissionError):
        svc.list_definitions(user, school_id=other_school)
    with pytest.raises(PermissionError):
        svc.run_simulation(user, school_id=other_school, definition_id=sample.id, inputs={"voltage": 1, "resistance": 1})
