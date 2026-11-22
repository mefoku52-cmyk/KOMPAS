class EnvironmentAdapter:
    def __init__(self, store):
        self.store = store

    def propose(self, entity_id, hypotheses, prediction, school_id=None):
        if not hypotheses:
            return []
        top = sorted(hypotheses, key=lambda h: h["confidence"], reverse=True)[0]
        suggestions = []
        text = top.get("hypothesis_text", "").lower()
        if "unáhlen" in text or "frustr" in text:
            suggestions.append({"type": "adjust_task_pace", "description": "Ponúknuť kratšiu úlohu alebo pauzu", "confidence": 0.6})
        if "konflikt" in text:
            suggestions.append({"type": "supervised_checkin", "description": "Pokojné overenie situácie dospelým", "confidence": 0.7})
        if not suggestions:
            suggestions.append({"type": "observe", "description": "Pokračovať v pozorovaní bez zásahu", "confidence": 0.5})
        self.store.audit("adaptation.proposed", {"entity_id": str(entity_id), "suggestions": suggestions}, entity_type="entity", entity_id=str(entity_id), school_id=school_id)
        return suggestions
