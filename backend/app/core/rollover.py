from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.shared.school import ClassGroup, Enrollment, SchoolYear


def rollover_school_year(
    db: Session,
    *,
    school_id: uuid.UUID,
    from_school_year_id: uuid.UUID,
    to_school_year_id: uuid.UUID,
    grade_max: int | None = None,
) -> dict[str, Any]:
    if from_school_year_id == to_school_year_id:
        raise ValueError("same_school_year")
    from_year = db.get(SchoolYear, from_school_year_id)
    to_year = db.get(SchoolYear, to_school_year_id)
    if from_year is None or from_year.school_id != school_id:
        raise ValueError("from_school_year_not_found")
    if to_year is None or to_year.school_id != school_id:
        raise ValueError("to_school_year_not_found")

    max_grade = settings.grade_max if grade_max is None else grade_max
    source_classes = db.execute(
        select(ClassGroup)
        .where(ClassGroup.school_id == school_id, ClassGroup.school_year_id == from_school_year_id)
        .order_by(ClassGroup.name.asc())
    ).scalars().all()

    moved = 0
    graduates = 0
    skipped = 0
    created_classes = 0
    reused_classes = 0

    for source_class in source_classes:
        enrollments = db.execute(
            select(Enrollment).where(
                Enrollment.school_id == school_id,
                Enrollment.school_year_id == from_school_year_id,
                Enrollment.class_group_id == source_class.id,
            )
        ).scalars().all()
        if source_class.grade >= max_grade:
            graduates += len(enrollments)
            continue

        target_class = db.execute(
            select(ClassGroup).where(
                ClassGroup.school_year_id == to_school_year_id,
                ClassGroup.name == source_class.name,
            )
        ).scalars().first()
        if target_class is None:
            target_class = ClassGroup(
                school_id=school_id,
                school_year_id=to_school_year_id,
                name=source_class.name,
                grade=source_class.grade + 1,
                is_demo=source_class.is_demo,
            )
            db.add(target_class)
            db.flush()
            created_classes += 1
        else:
            reused_classes += 1

        for enrollment in enrollments:
            existing = db.execute(
                select(Enrollment).where(
                    Enrollment.school_year_id == to_school_year_id,
                    Enrollment.student_user_id == enrollment.student_user_id,
                )
            ).scalars().first()
            if existing is not None:
                skipped += 1
                continue
            db.add(Enrollment(
                school_id=school_id,
                school_year_id=to_school_year_id,
                class_group_id=target_class.id,
                student_user_id=enrollment.student_user_id,
                is_demo=enrollment.is_demo,
            ))
            moved += 1
    db.flush()
    return {
        "school_id": str(school_id),
        "from_school_year_id": str(from_school_year_id),
        "to_school_year_id": str(to_school_year_id),
        "grade_max": max_grade,
        "source_classes": len(source_classes),
        "created_classes": created_classes,
        "reused_classes": reused_classes,
        "moved_students": moved,
        "graduates": graduates,
        "skipped_existing": skipped,
    }
