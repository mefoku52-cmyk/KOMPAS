from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database.session import get_db

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
async def get_intervention_message(student_id: str, db: Session = Depends(get_db)):
    """
    Frontend volá tento endpoint pri načítaní dashboardu.
    Ak AI detekovala problém, vráti neutrálnu správu. Inak vráti null.
    """
    from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService
    service = WellbeingAnalyticService(db_session=db)
    message = service.get_latest_intervention_message(student_id)
    
    return {
        "student_id": student_id,
        "has_intervention": message is not None,
        "message": message,
        "sender": "kompas_ai_companion"
    }
