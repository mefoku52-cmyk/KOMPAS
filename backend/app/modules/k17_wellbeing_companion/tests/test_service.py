import pytest
from unittest.mock import MagicMock, patch
import uuid

from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService
from app.modules.k17_wellbeing_companion.repository.models import BehavioralState
from app.core.events.bus import DomainEvent
from app.modules.k17_wellbeing_companion.events.handlers import on_AnswerEvaluated

def test_cognitive_overload_detection():
    mock_db = MagicMock()
    mock_history = [
        MagicMock(metrics={"time_taken_sec": 10.0}),
        MagicMock(metrics={"time_taken_sec": 12.0}),
        MagicMock(metrics={"time_taken_sec": 8.0})
    ]
    mock_db.query().filter().order_by().limit().all.return_value = mock_history
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    service = WellbeingAnalyticService(db_session=mock_db)
    
    obs = service.record_observation(
        student_id="test-student-123",
        event_type="mission_answer",
        metrics={"is_correct": False, "time_taken_sec": 20.0, "consecutive_errors": 3}
    )
    
    assert obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD
    assert obs.alert_level == 2
    mock_db.add.assert_called_once()

def test_avoidance_detection():
    mock_db = MagicMock()
    mock_db.query().filter().order_by().limit().all.return_value = []
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    service = WellbeingAnalyticService(db_session=mock_db)
    
    obs = service.record_observation(
        student_id="test-student-123",
        event_type="mission_answer",
        metrics={"is_correct": False, "time_taken_sec": 2.0, "consecutive_errors": 1}
    )
    
    assert obs.inferred_state == BehavioralState.AVOIDANCE
    assert obs.alert_level == 2

def test_event_handler_integration_with_domain_event():
    """
    Overí, že handler správne spracuje DomainEvent a použije current_session().
    Simuluje scenár, kde žiak odpovedá príliš rýchlo po chybe (Avoidance).
    """
    mock_db = MagicMock()
    mock_db.query().filter().order_by().limit().all.return_value = []
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    # Mockujeme current_session, aby vrátila našu mock_db
    with patch('app.modules.k17_wellbeing_companion.events.handlers.current_session', return_value=mock_db):
        event = DomainEvent(
            event_type="AnswerEvaluated",
            school_id=uuid.uuid4(),
            payload={
                "student_id": "test-student-456",
                "mission_id": "mission-1",
                "is_correct": False,
                "time_taken_sec": 2.0,
                "consecutive_errors": 1
            }
        )
        
        # Spustenie handlera (nesmie vyhodiť výnimku)
        on_AnswerEvaluated(event)
        
        # Overenie, že handler zapisoval do DB
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_not_called()

def test_get_latest_intervention_message_returns_neutral_text():
    """
    Overí, že service vráti neutrálnu správu, ak je alert_level >= 2.
    """
    from datetime import timedelta
    mock_db = MagicMock()
    
    # Simulujeme záznam z pred 5 minút s COGNITIVE_OVERLOAD
    recent_obs = MagicMock()
    recent_obs.inferred_state = BehavioralState.COGNITIVE_OVERLOAD
    recent_obs.alert_level = 2
    
    mock_db.query().filter().order_by().first.return_value = recent_obs

    service = WellbeingAnalyticService(db_session=mock_db)
    msg = service.get_latest_intervention_message("test-student-999")
    
    assert msg is not None
    assert "bežná súčasť učenia" in msg # Overenie neutrálneho, neodsudzujúceho tónu
    assert "Si šikovný" not in msg # Overenie, že tam nie je manipulácia/chvála


def test_ignores_health_and_family_metrics():
    from unittest.mock import MagicMock
    from app.modules.k17_wellbeing_companion.services.service import WellbeingAnalyticService
    from app.modules.k17_wellbeing_companion.repository.models import BehavioralState

    mock_db = MagicMock()
    mock_db.query().filter().order_by().limit().all.return_value = []
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    service = WellbeingAnalyticService(db_session=mock_db)
    obs = service.record_observation(
        student_id="test-health-1",
        event_type="mission_answer",
        metrics={"is_correct": False, "time_taken_sec": 2.0, "consecutive_errors": 1, "health": "sick", "weight": 50, "family_status": "divorced"},
    )
    assert obs.inferred_state == BehavioralState.AVOIDANCE
