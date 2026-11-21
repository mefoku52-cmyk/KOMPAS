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
async def get_student_state(student_id: str, db: Session = Depends(get_db)):
    """
    Vrátí aktuálny odhadovaný psychický stav žiaka na základe pozorovaní.
    Neobsahuje hodnotenie, iba objektívne metriky (napr. tempo, pauzy).
    """
    # Implementácia bude volať WellbeingService.get_current_state
    return {"student_id": student_id, "state": "neutral", "indicators": []}

@router.post("/students/{student_id}/intervention")
async def request_intervention(student_id: str, db: Session = Depends(get_db)):
    """
    Vygeneruje neutrálny textový podnet pre K-14 (Communication Center).
    Príklad: 'Všimol som si zmenu v tempe. Chcete pokračovať, alebo si dať 2-minútovú pauzu?'
    """
    # Implementácia bude volať WellbeingService.generate_neutral_prompt
    return {"message": "Pozorujem aktivitu. Ako sa cítite?", "suggested_action": "check_in"}

@router.get("/students/{student_id}/intervention-message")
async def get_intervention_message(
    student_id: str,
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
    
    # Kontrolovať oprávnenie
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
            raise HTTPException(status_code=403, detail="not_teacher_of_student")
    else:
        raise HTTPException(status_code=403, detail="insufficient_permissions")
    
    service = WellbeingAnalyticService(db_session=db)
    message = service.get_latest_intervention_message(student_id)
    
    return {
        "student_id": student_id,
        "has_intervention": message is not None,
        "message": message,
        "sender": "kompas_ai_companion"
    }
