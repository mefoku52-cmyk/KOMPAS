from app.shared.types import utc_now, new_uuid


class ContextMemoryService:
    def __init__(self, store):
        self.store = store

    def record(self, entity_type, entity_id, context_type, context, source_event_id=None, school_id=None, confidence=None):
        m = {
            "id": new_uuid(), "entity_type": entity_type, "entity_id": str(entity_id), "context_type": context_type,
            "context": context, "confidence": confidence, "valid_from": utc_now(), "valid_to": None,
            "source_event_id": source_event_id, "source_record_ref": f"event:{source_event_id}" if source_event_id else None,
            "school_id": school_id,
        }
        rec = self.store.save_memory(m)
        self.store.audit("memory.record", {"entity_type": entity_type, "entity_id": str(entity_id), "context_type": context_type}, entity_type=entity_type, entity_id=str(entity_id), school_id=school_id)
        return rec

    def get_context(self, entity_type, entity_id, limit=20):
        return self.store.get_memory(entity_type, entity_id, limit=limit)
