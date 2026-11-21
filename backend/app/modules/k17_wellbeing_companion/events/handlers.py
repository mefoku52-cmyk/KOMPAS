import logging
from app.core.events.bus import DomainEvent, current_session
from app.core.database.session import SessionLocal
from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService

logger = logging.getLogger("kompas.k17_wellbeing")

def on_AnswerEvaluated(event: DomainEvent) -> None:
    """
    Handler pre udalosť z K-04 (Missions).
    Očakávaný event_type: "AnswerEvaluated"
    
    Psychologický kontext: Hľadáme vzorce správania (nie emócie). 
    Rýchle chyby = únik. Pomalé chyby = kognitívne preťaženie.
    """
    if event.event_type != "AnswerEvaluated":
        return

    payload = event.payload
    student_id = payload.get("student_id")
    
    if not student_id:
        logger.warning("K17: Missing student_id in AnswerEvaluated event")
        return

    # SENIOR PRÍSTUP: Použi existujúcu session z kontextu, aby sme sa vyhli deadlocku 
    # a čítali konzistentný stav. Ak nie je k dispozícii, vytvor novú.
    db = current_session()
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        service = WellbeingAnalyticService(db_session=db)
        
        # 1. Zaznamenaj pozorovanie a vypočítaj stav
        obs = service.record_observation(
            student_id=str(student_id),
            event_type="mission_answer",
            metrics={
                "is_correct": bool(payload.get("is_correct", False)),
                "time_taken_sec": float(payload.get("time_taken_sec", 0.0)),
                "consecutive_errors": int(payload.get("consecutive_errors", 0))
            }
        )
        
        # 2. Ak je alert_level >= 2, priprav intervenciu
        if obs.alert_level >= 2:
            intervention_text = service.get_intervention_prompt(str(student_id))
            if intervention_text:
                logger.warning(
                    f"K17 INTERVENTION TRIGGERED | Student: {student_id} | "
                    f"State: {obs.inferred_state.value} | Alert: {obs.alert_level}"
                )
                
                # PRÍPRAVA NA K-14 INTEGRÁCIU:
                # Namiesto priameho volania API vygenerujeme novú DomainEvent.
                # Tým zachovávame čistú event-driven architektúru.
                # from app.core.events.bus import bus
                # bus.publish(DomainEvent(
                #     event_type="communication.direct_message",
                #     school_id=event.school_id,
                #     payload={
                #         "recipient_id": str(student_id),
                #         "sender_type": "ai_companion",
                #         "message": intervention_text
                #     }
                # ), db=db)
                
    except Exception as e:
        logger.error(f"K17 Wellbeing handler failed: {e}", exc_info=True)
    finally:
        # Uzatvorenie session iba ak sme ju my vytvorili
        if close_session and db is not None:
            db.close()


def register(bus) -> None:
    bus.subscribe("AnswerEvaluated", on_AnswerEvaluated)
