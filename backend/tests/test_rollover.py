from __future__ import annotations

import uuid

import pytest

from app.core.rollover import rollover_school_year
from app.shared.identity import User
from app.shared.school import ClassGroup, Enrollment, School, SchoolYear


def _seed(db):
    school = School(name=f"Rollover-{uuid.uuid4()}")
    db.add(school)
    db.flush()
    from_year = SchoolYear(school_id=school.id, name="2025/2026")
    to_year = SchoolYear(school_id=school.id, name="2026/2027")
    db.add_all([from_year, to_year])
    db.flush()
    fifth = ClassGroup(school_id=school.id, school_year_id=from_year.id, name="5.A", grade=5)
    ninth = ClassGroup(school_id=school.id, school_year_id=from_year.id, name="9.A", grade=9)
    db.add_all([fifth, ninth])
    db.flush()
    students = []
    for index, class_group in enumerate((fifth, fifth, ninth)):
        user = User(
            id=uuid.uuid4(), school_id=school.id, username=f"student-{index}-{uuid.uuid4()}",
            full_name=f"Student {index}", password_hash="x", is_demo=True,
        )
        db.add(user)
        db.flush()
        db.add(Enrollment(
            school_id=school.id, school_year_id=from_year.id,
            class_group_id=class_group.id, student_user_id=user.id, is_demo=True,
        ))
        students.append((user, class_group))
    db.commit()
    return school, from_year, to_year, fifth, ninth, students


def test_rollover_moves_students_and_keeps_history(db_session):
    school, from_year, to_year, fifth, ninth, students = _seed(db_session)
    result = rollover_school_year(
        db_session, school_id=school.id, from_school_year_id=from_year.id, to_school_year_id=to_year.id, grade_max=9,
    )
    db_session.commit()
    assert result["moved_students"] == 2
    assert result["graduates"] == 1
    assert result["created_classes"] == 1
    assert result["source_classes"] == 2

    target = db_session.query(ClassGroup).filter_by(school_year_id=to_year.id, name="5.A").one()
    assert target.grade == 6
    target_enrollments = db_session.query(Enrollment).filter_by(school_year_id=to_year.id).all()
    assert len(target_enrollments) == 2
    assert {e.student_user_id for e in target_enrollments} == {students[0][0].id, students[1][0].id}
    assert db_session.query(Enrollment).filter_by(school_year_id=to_year.id, class_group_id=ninth.id).count() == 0

    history = db_session.query(Enrollment).filter_by(school_year_id=from_year.id).all()
    assert len(history) == 3
    assert db_session.query(ClassGroup).filter_by(school_year_id=from_year.id).count() == 2


def test_rollover_is_idempotent(db_session):
    school, from_year, to_year, _, _, _ = _seed(db_session)
    first = rollover_school_year(
        db_session, school_id=school.id, from_school_year_id=from_year.id, to_school_year_id=to_year.id, grade_max=9,
    )
    db_session.commit()
    second = rollover_school_year(
        db_session, school_id=school.id, from_school_year_id=from_year.id, to_school_year_id=to_year.id, grade_max=9,
    )
    db_session.commit()
    assert second["moved_students"] == 0
    assert second["skipped_existing"] == 2
    assert second["created_classes"] == 0
    assert second["graduates"] == 1
    assert db_session.query(Enrollment).filter_by(school_year_id=to_year.id).count() == first["moved_students"]


def test_rollover_rejects_invalid_years(db_session):
    school, from_year, to_year, _, _, _ = _seed(db_session)
    with pytest.raises(ValueError, match="same_school_year"):
        rollover_school_year(
            db_session, school_id=school.id, from_school_year_id=from_year.id, to_school_year_id=from_year.id,
        )
    other_school = School(name=f"Other-{uuid.uuid4()}")
    db_session.add(other_school)
    db_session.flush()
    with pytest.raises(ValueError, match="from_school_year_not_found"):
        rollover_school_year(
            db_session, school_id=other_school.id, from_school_year_id=from_year.id, to_school_year_id=to_year.id,
        )
