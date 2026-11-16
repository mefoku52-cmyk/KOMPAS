import uuid

import pytest

from app.modules.k07_professional_library.services.service import K07Service
from app.shared.identity import User
from app.shared.school import School
from app.shared.storage import LocalFileStorage
from app.shared.types import Principal, Role


def _setup(db_session, tmp_path):
    school_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    other_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"S-{school_id}"))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x"))
    db_session.add(User(id=other_id, school_id=school_id, username=f"o-{other_id}", full_name="O", password_hash="x"))
    db_session.commit()
    storage = LocalFileStorage(tmp_path / "storage")
    return school_id, teacher_id, other_id, storage


def test_k07_owner_can_manage_versions_tags_and_archive(db_session, tmp_path):
    school_id, teacher_id, _, storage = _setup(db_session, tmp_path)
    svc = K07Service(db_session, storage=storage)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    item = svc.create_item(teacher, school_id=school_id, owner_teacher_user_id=teacher_id, title="Priprava")
    svc.add_version(teacher, item.id, version_number=1, content_bytes=b"v1", content_text="t1")
    svc.add_version(teacher, item.id, version_number=2, content_text="t2")
    svc.add_tag(teacher, item.id, "matematika")
    svc.archive_item(teacher, item.id)
    db_session.commit()
    items = svc.list_items(teacher, school_id=school_id, owner_teacher_user_id=teacher_id, include_archived=True)
    assert len(items) == 1 and items[0].archived is True
    versions = svc.list_versions(teacher, item.id)
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].storage_key is not None
    assert storage.read(versions[0].storage_key) == b"v1"


def test_k07_other_teacher_denied(db_session, tmp_path):
    school_id, teacher_id, other_id, storage = _setup(db_session, tmp_path)
    svc = K07Service(db_session, storage=storage)
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    item = svc.create_item(teacher, school_id=school_id, owner_teacher_user_id=teacher_id, title="X")
    db_session.commit()
    other = Principal(user_id=other_id, role=Role.TEACHER, school_id=school_id)
    with pytest.raises(PermissionError):
        svc.list_versions(other, item.id)
    with pytest.raises(PermissionError):
        svc.add_tag(other, item.id, "x")
