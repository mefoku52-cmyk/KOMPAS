from __future__ import annotations

from app.shared.types import utc_now, new_uuid
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict
from .safety.service import SafetyGovernance
from .perception.service import PerceptionEngine
from .memory.service import ContextMemoryService
from .reasoning.service import ReasoningEngine
from .prediction.service import PredictionEngine
from .initiative.service import InitiativeEngine
from .communication.service import CommunicationEngine
from .adaptation.service import EnvironmentAdapter
from .evaluation.service import OutcomeEvaluator


class IntelligenceOrchestrator:
    def __init__(self, db):
        self.db = db
        self.store = ILStore(db)
        self.safety = SafetyGovernance()
        self.perception = PerceptionEngine(self.store)
        self.memory = ContextMemoryService(self.store)
        self.reasoning = ReasoningEngine(self.store)
        self.prediction = PredictionEngine(self.store)
        self.initiative = InitiativeEngine(self.store, self.safety)
        self.communication = CommunicationEngine(self.store, self.safety, db)
        self.adaptation = EnvironmentAdapter(self.store)
        self.evaluation = OutcomeEvaluator(self.store)

    @staticmethod
    def _coerce_uuid(value):
        if value is None:
            return None
        if isinstance(value, __import__('uuid').UUID):
            return value
        try:
            return __import__('uuid').UUID(str(value))
        except Exception:
            return None

    def process_event(self, event_type, payload, source="api", school_id=None, correlation_id=None, event_id=None, locale="sk"):
        school_id = self._coerce_uuid(school_id)
        correlation_id = self._coerce_uuid(correlation_id)
        event_id = self._coerce_uuid(event_id)
        ing = self.perception.ingest(event_type, payload, source=source, school_id=school_id, correlation_id=correlation_id, event_id=event_id)
        entity_type = payload.get("entity_type") or ("student" if payload.get("student_user_id") or payload.get("student") else "group")
        entity_id = payload.get("entity_id") or payload.get("student_user_id") or payload.get("student") or "unknown"
        if ing["status"] == "duplicate":
            self.store.audit("perception.duplicate_ignored", {"event_id": str(ing["event_id"]), "entity_id": str(entity_id), "reason": "same event_id redelivered"}, entity_type=entity_type, entity_id=str(entity_id), school_id=school_id)
            return {"status": "duplicate", "event_id": str(ing["event_id"]), "duplicate": True, "initiative": None, "hypotheses": [], "prediction": None, "communication": None, "adaptations": [], "outcome": None, "message": "duplicitná udalosť — preskočené"}

        ev = ing["event"]
        mem = self.memory.record(entity_type, entity_id, "signal", {"event_type": event_type, **payload}, source_event_id=ev.event_id, school_id=school_id, confidence=0.6)
        context = self.memory.get_context(entity_type, entity_id)
        hypotheses = self.reasoning.evaluate(entity_type, entity_id, ev, context, school_id=school_id)
        prediction = self.prediction.predict(entity_id, hypotheses, school_id=school_id)
        initiative = self.initiative.decide(entity_type, entity_id, ev, hypotheses, prediction, school_id=school_id)
        communication = self.communication.compose_and_send(initiative, locale=locale)
        adaptations = self.adaptation.propose(entity_id, hypotheses, prediction, school_id=school_id)
        outcome = None
        if communication:
            outcome = self.evaluation.evaluate(initiative.id, outcome="pending", metrics={"simulated": True}, feedback_source="system", school_id=school_id)

        return {
            "status": "processed",
            "event": _to_dict(ev),
            "memory": _to_dict(mem),
            "hypotheses": hypotheses,
            "prediction": prediction,
            "initiative": _to_dict(initiative),
            "communication": _to_dict(communication) if communication else None,
            "adaptations": adaptations,
            "outcome": _to_dict(outcome) if outcome else None,
        }
