import app.main  # noqa: F401  # ensures K-17 handler registration
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
def test_intervention_endpoint_requires_authorization(db_session):
    """
    Overí, že endpoint /intervention-message vyžaduje autorizáciu.
    Žiak A nesmie vidieť dáta žiaka B (očakáva sa 403 Forbidden).
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security.auth import create_access_token
    from app.shared.types import Role
    import uuid
    
    client = TestClient(app)
    
    # Vytvoriť dvoch fiktívnych žiakov a školu
    student_a_id = uuid.uuid4()
    student_b_id = uuid.uuid4()
    school_id = uuid.uuid4()
    
    # Vytvoriť token pre žiaka A (používame presnú signatúru z test_core_phase1.py)
    token_a = create_access_token(student_a_id, Role.STUDENT, school_id)
    
    # Pokus o získanie dát žiaka B s tokenom žiaka A
    response = client.get(
        f"/k17/wellbeing/students/{student_b_id}/intervention-message",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    # Očakávame 403 Forbidden, pretože principal.user_id != student_b_id
    # a žiak nemá rolu parent ani teacher.
    assert response.status_code == 403, f"Očakávaný 403, ale dostali sme {response.status_code}: {response.text}"

def test_intervention_endpoint_requires_authorization(db_session):
    """
    Overí, že endpoint /intervention-message vyžaduje autorizáciu.
    Žiak A nesmie vidieť dáta žiaka B (očakáva sa 403 Forbidden).
    Používa dependency_overrides na obídenie DB lookupu pre fake UUID.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security.auth import get_current_principal
    from app.core.permissions.policy import Principal
    from app.shared.types import Role  # Alebo kde je definovaný Role enum
    import uuid

    client = TestClient(app)
    
    student_a_id = uuid.uuid4()
    student_b_id = uuid.uuid4()
    school_id = uuid.uuid4()

    # 1. Override dependency: Podstrčíme fake, ale štruktúrne platný Principal pre Žiaka A
    def override_get_principal():
        return Principal(user_id=student_a_id, role=Role.STUDENT, school_id=school_id)

    app.dependency_overrides[get_current_principal] = override_get_principal

    try:
        # 2. Pokus o získanie dát žiaka B s principalom žiaka A
        # Neposielame ani token, lebo dependency je override-nutá
        response = client.get(f"/k17/wellbeing/students/{student_b_id}/intervention-message")

        # 3. Očakávame 403 Forbidden, lebo principal.user_id (A) != student_b_id (B)
        # a role je STUDENT (nemá právo GUARDIAN_OF ani TEACHES_CLASS)
        assert response.status_code == 403, f"Očakávaný 403, ale dostali sme {response.status_code}: {response.text}"
        
    finally:
        # 4. Vyčistíme override, aby neovplyvnil ďalšie testy
        app.dependency_overrides.clear()
