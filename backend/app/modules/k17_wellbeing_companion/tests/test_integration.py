import pytest
import uuid
from app.core.events.bus import DomainEvent, bus
from app.modules.k17_wellbeing_companion.repository.models import WellbeingObservation, BehavioralState

def test_k17_catches_k04_answer_evaluated_event(db_session):
    """
    End-to-end test: Simuluje udalosť z K-04 a overuje, že K-17 ju zachytí a správne vyhodnotí.
    Scenár: Žiak odpovedá nesprávne a veľmi rýchlo (2.0 sekundy) po 1 predchádzajúcej chybe.
    Očakávaný výsledok: Stav AVOIDANCE, alert_level 2.
    """
    # 0. SENIOR FIX: Explicitne vytvor tabuľku pre tento test, ak neexistuje.
    # Rieši problém, keď conftest.py nepozná nový model pri create_all().
    WellbeingObservation.__table__.create(db_session.bind, checkfirst=True)

    # 1. Simuluj udalosť presne tak, ako ju vysiela K-04
    event = DomainEvent(
        event_type="AnswerEvaluated",
        school_id=uuid.uuid4(),
        payload={
            "student_id": "test-student-e2e-999",
            "mission_id": "mission-xyz",
            "is_correct": False,
            "time_taken_sec": 2.0,
            "consecutive_errors": 1
        }
    )
    
    # 2. Publikuj udalosť cez bus (toto automaticky spustí náš registrovaný handler on_AnswerEvaluated)
    bus.publish(event, db=db_session)
    
    # 3. Over, že K-17 handler zachytil udalosť a vytvoril záznam v DB
    obs = db_session.query(WellbeingObservation).filter(
        WellbeingObservation.student_id == "test-student-e2e-999"
    ).first()
    
    # 4. Asertácie
    assert obs is not None, "Záznam nebol vytvorený v databáze"
    assert obs.event_type == "mission_answer"
    assert obs.inferred_state == BehavioralState.AVOIDANCE, f"Očakávaný AVOIDANCE, ale je {obs.inferred_state}"
    assert obs.alert_level == 2, f"Očakávaný alert_level 2, ale je {obs.alert_level}"
    assert obs.metrics["is_correct"] is False
    assert obs.metrics["time_taken_sec"] == 2.0
