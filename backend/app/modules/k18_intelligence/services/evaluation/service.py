from app.shared.types import utc_now, new_uuid


class OutcomeEvaluator:
    def __init__(self, store):
        self.store = store

    def evaluate(self, initiative_id, outcome="unknown", metrics=None, feedback_source="system", school_id=None):
        o = {"id": new_uuid(), "initiative_id": initiative_id, "outcome": outcome, "metrics": metrics or {}, "feedback_source": feedback_source, "evaluated_at": utc_now(), "school_id": school_id}
        rec = self.store.save_outcome(o)
        self.store.audit("outcome.evaluated", {"initiative_id": str(initiative_id), "outcome": outcome}, entity_type="initiative", entity_id=str(initiative_id), school_id=school_id)
        return rec
