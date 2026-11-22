from app.shared.types import utc_now, new_uuid


class PerceptionEngine:
    def __init__(self, store):
        self.store = store

    def ingest(self, event_type, payload, source="api", school_id=None, correlation_id=None, event_id=None):
        event_id = event_id or new_uuid()
        existing = self.store.get_event_by_event_id(event_id)
        if existing:
            self.store.audit("perception.duplicate", {"event_id": str(event_id), "event_type": event_type, "payload": payload}, entity_type="event", entity_id=str(event_id), school_id=school_id)
            return {"status": "duplicate", "event_id": event_id, "event": existing}
        ev = {
            "event_id": event_id,
            "event_type": event_type,
            "source": source,
            "payload": payload,
            "occurred_at": payload.get("occurred_at") or utc_now(),
            "processed_at": utc_now(),
            "processing_status": "processed",
            "school_id": school_id,
            "correlation_id": correlation_id,
        }
        rec = self.store.save_event(ev)
        if rec is None:
            return {"status": "duplicate", "event_id": event_id}
        self.store.audit("perception.ingest", {"event_id": str(event_id), "event_type": event_type, "payload": payload}, entity_type="event", entity_id=str(event_id), school_id=school_id)
        return {"status": "ingested", "event_id": event_id, "event": rec}
