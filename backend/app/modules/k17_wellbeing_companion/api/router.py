from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.core.permissions.policy import Principal, Scope
from fastapi import HTTPException, status

router = APIRouter(prefix="/k17/wellbeing", tags=["Wellbeing Companion"])

@router.get("/status")
async def get_status():
    """
    Overenie dostupnosti modulu.
    """
    return {
        "module": "k17_wellbeing_companion", 
        "status": "active", 
        "vision": "neutral_observation_no_manipulation"
    }

@router.get("/students/{student_id}/state")
async def get_student_state(
    student_id: str,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Stav ziaka je interny signal pre ucitela/vedenie. Ziak a rodic ho nevidia.
    """
    import uuid
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_student_id")

    if principal.user_id == student_uuid:
        raise HTTPException(status_code=403, detail="student_cannot_view_state")
    if principal.role and principal.role.value == "parent":
        raise HTTPException(status_code=403, detail="parent_cannot_view_state")
    if principal.role and principal.role.value == "teacher":
        from sqlalchemy import select
        from app.core.database.session import Base
        from app.shared.school import Enrollment
        table = Base.metadata.tables.get("school_class_teacher")
        enrollments = db.execute(
            select(Enrollment).where(
                Enrollment.student_user_id == student_uuid,
                Enrollment.school_id == principal.school_id,
            )
        ).scalars().all()
        teaches = False
        if enrollments and table is not None:
            for enr in enrollments:
                row = db.execute(
                    select(table.c.id).where(
                        table.c.school_id == principal.school_id,
                        table.c.class_group_id == enr.class_group_id,
                        table.c.teacher_user_id == principal.user_id,
                    )
                ).first()
                if row is not None:
                    teaches = True
                    break
        if not teaches:
            raise HTTPException(status_code=403, detail="not_teacher_of_student")
    elif principal.role and principal.role.value == "leadership":
        pass
    else:
        raise HTTPException(status_code=403, detail="insufficient_permissions")

    from app.core.audit.logger import write as audit_write
    audit_write(db, principal, "k17.get_student_state", f"k17_wellbeing_observation:student:{student_uuid}", None, "success", {})

    return {"student_id": student_id, "state": "neutral", "indicators": []}

@router.post("/students/{student_id}/intervention")
async def request_intervention(
    student_id: str,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Return a neutral check-in only to an authorized student or their school staff."""
    import uuid
    from sqlalchemy import select
    from app.core.database.session import Base
    from app.shared.identity import GuardianLink
    from app.shared.school import Enrollment

    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_student_id")

    allowed = principal.user_id == student_uuid
    role = principal.role.value if principal.role else None
    if not allowed and role == "parent":
        allowed = db.execute(select(GuardianLink.id).where(
            GuardianLink.guardian_user_id == principal.user_id,
            GuardianLink.child_user_id == student_uuid,
            GuardianLink.school_id == principal.school_id,
        )).first() is not None
    elif not allowed and role == "teacher":
        assignments = Base.metadata.tables.get("school_class_teacher")
        enrollments = db.execute(select(Enrollment.class_group_id).where(
            Enrollment.student_user_id == student_uuid, Enrollment.school_id == principal.school_id,
        )).all()
        if assignments is not None:
            allowed = any(db.execute(select(assignments.c.id).where(
                assignments.c.school_id == principal.school_id,
                assignments.c.class_group_id == row[0],
                assignments.c.teacher_user_id == principal.user_id,
            )).first() is not None for row in enrollments)
    elif not allowed and role == "leadership":
        from app.shared.identity import User
        target = db.get(User, student_uuid)
        allowed = bool(target and target.school_id == principal.school_id)

    if not allowed:
        raise HTTPException(status_code=403, detail="student_access_denied")
    return {"student_id": str(student_uuid), "message": "Pozorujem aktivitu. Ako sa cítite?", "suggested_action": "check_in"}

@router.get("/students/{student_id}/intervention-message")
async def get_intervention_message(
    student_id: str,
    purpose: str | None = None,
    locale: str = "sk",
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)
):
    """
    Frontend volá tento endpoint pri načítaní dashboardu.
    Autorizácia: žiak (SELF), rodič (GUARDIAN_OF), učiteľ (TEACHES_CLASS).
    """
    import uuid
    from app.core.permissions.policy import authorize, Scope
    from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService
    
    # Overiť, že student_id je platné UUID
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_student_id")
    
    resource = f"k17_wellbeing_observation:student:{student_uuid}"
    action = "k17.get_intervention_message"

    # 1. SELF: žiak môže vidieť svoje vlastné dáta
    if principal.user_id == student_uuid:
        pass  # OK
    # 2. GUARDIAN_OF: rodič môže vidieť dáta svojho dieťaťa
    elif principal.role and principal.role.value == "parent":
        from app.shared.identity import GuardianLink
        link = db.query(GuardianLink).filter(
            GuardianLink.guardian_user_id == principal.user_id,
            GuardianLink.child_user_id == student_uuid
        ).first()
        if not link:
            from app.core.audit.logger import write as audit_write
            audit_write(db, principal, action, resource, purpose, "denied", {"reason": "not_guardian_of_student"})
            raise HTTPException(status_code=403, detail="not_guardian_of_student")
    # 3. TEACHES_CLASS: učiteľ môže vidieť dáta žiakov zo svojej triedy
    elif principal.role and principal.role.value == "teacher":
        from sqlalchemy import select
        from app.core.database.session import Base
        from app.shared.school import Enrollment
        table = Base.metadata.tables.get("school_class_teacher")
        enrollments = db.execute(
            select(Enrollment).where(
                Enrollment.student_user_id == student_uuid,
                Enrollment.school_id == principal.school_id,
            )
        ).scalars().all()
        teaches = False
        if enrollments and table is not None:
            for enr in enrollments:
                row = db.execute(
                    select(table.c.id).where(
                        table.c.school_id == principal.school_id,
                        table.c.class_group_id == enr.class_group_id,
                        table.c.teacher_user_id == principal.user_id,
                    )
                ).first()
                if row is not None:
                    teaches = True
                    break
        if not teaches:
            from app.core.audit.logger import write as audit_write
            audit_write(db, principal, action, resource, purpose, "denied", {"reason": "not_teacher_of_student"})
            raise HTTPException(status_code=403, detail="not_teacher_of_student")
    else:
        from app.core.audit.logger import write as audit_write
        audit_write(db, principal, action, resource, purpose, "denied", {"reason": "insufficient_permissions"})
        raise HTTPException(status_code=403, detail="insufficient_permissions")
    
    service = WellbeingAnalyticService(db_session=db)
    message = service.get_latest_intervention_message(student_id, locale=locale)

    from app.core.audit.logger import write as audit_write
    audit_write(db, principal, action, resource, purpose, "success", {"has_intervention": message is not None})

    return {
        "student_id": student_id,
        "has_intervention": message is not None,
        "message": message,
        "sender": "kompas_ai_companion"
    }


@router.get("/classes/{class_id}/signals")
async def get_class_signals(
    class_id: str,
    hours: int = 24,
    locale: str = "sk",
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    import uuid
    from sqlalchemy import select
    from app.core.database.session import Base
    from app.shared.school import Enrollment
    from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService

    try:
        class_uuid = uuid.UUID(class_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_class_id")

    if not (principal.role and principal.role.value == "teacher"):
        raise HTTPException(status_code=403, detail="teacher_only")

    table = Base.metadata.tables.get("school_class_teacher")
    assigned = False
    if table is not None:
        row = db.execute(
            select(table.c.id).where(
                table.c.class_group_id == class_uuid,
                table.c.teacher_user_id == principal.user_id,
                table.c.school_id == principal.school_id,
            )
        ).first()
        assigned = row is not None
    if not assigned:
        raise HTTPException(status_code=403, detail="not_teacher_of_class")

    enrollments = db.execute(
        select(Enrollment).where(
            Enrollment.class_group_id == class_uuid,
            Enrollment.school_id == principal.school_id,
        )
    ).scalars().all()
    student_ids = [e.student_user_id for e in enrollments]

    service = WellbeingAnalyticService(db_session=db)
    signals = service.get_class_signals(student_ids, hours=hours, locale=locale)

    from app.core.audit.logger import write as audit_write
    audit_write(db, principal, "k17.get_class_signals", f"school_class_group:{class_uuid}", None, "success", {"count": len(signals)})

    return {"class_id": class_id, "signals": signals}


@router.post("/students/{student_id}/signals/dismiss")
async def dismiss_signal(
    student_id: str,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_student_id")

    if not (principal.role and principal.role.value == "teacher"):
        raise HTTPException(status_code=403, detail="teacher_only")

    from app.core.audit.logger import write as audit_write
    audit_write(db, principal, "k17.dismiss_signal", f"k17_wellbeing_observation:student:{student_uuid}", None, "success", {"dismissed": True})

    return {"student_id": student_id, "dismissed": True}


@router.get("/parent/dashboard")
async def get_parent_dashboard(
    locale: str = "sk",
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if not (principal.role and principal.role.value == "parent"):
        raise HTTPException(status_code=403, detail="parent_only")

    from app.shared.identity import GuardianLink
    links = db.query(GuardianLink).filter(GuardianLink.guardian_user_id == principal.user_id).all()
    child_ids = [l.child_user_id for l in links]

    from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService
    service = WellbeingAnalyticService(db_session=db)
    children = []
    for cid in child_ids:
        messages = service.get_child_messages(str(cid), locale=locale)
        children.append({"child_user_id": str(cid), "messages": messages})

    from app.core.audit.logger import write as audit_write
    audit_write(db, principal, "k17.get_parent_dashboard", "k17_wellbeing_observation:children", None, "success", {"child_count": len(children)})

    return {"children": children}
