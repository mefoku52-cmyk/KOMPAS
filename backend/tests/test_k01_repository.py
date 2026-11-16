import uuid

from app.modules.k01_learning_profile.repository.repository import K01Repository
from app.shared.identity import User
from app.shared.school import School, SchoolYear


def test_k01_repository_history(db_session):
    school_id = uuid.uuid4()
    year1 = uuid.uuid4()
    year2 = uuid.uuid4()
    student_id = uuid.uuid4()
    db_session.add(School(id=school_id, name="S1"))
    db_session.add(SchoolYear(id=year1, school_id=school_id, name="2025/26"))
    db_session.add(SchoolYear(id=year2, school_id=school_id, name="2026/27"))
    db_session.add(User(id=student_id, school_id=school_id, username="s", full_name="S", password_hash="x"))
    db_session.commit()

    repo = K01Repository(db_session)
    repo.create_profile(school_id=school_id, student_user_id=student_id, school_year_id=year1, grade=5, version=1)
    repo.create_profile(school_id=school_id, student_user_id=student_id, school_year_id=year1, grade=5, version=2, label="updated")
    repo.create_profile(school_id=school_id, student_user_id=student_id, school_year_id=year2, grade=6, version=1)
    db_session.commit()

    hist = repo.list_history(student_id, school_id)
    assert len(hist) == 3
    assert [h.grade for h in hist] == [5, 5, 6]
    assert [h.version for h in hist] == [1, 2, 1]
