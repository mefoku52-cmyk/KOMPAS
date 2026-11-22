from app.shared.types import utc_now, new_uuid


class PredictionEngine:
    def __init__(self, store):
        self.store = store

    def predict(self, entity_id, hypotheses, school_id=None):
        if not hypotheses:
            return None
        top = sorted(hypotheses, key=lambda h: h["confidence"], reverse=True)[0]
        conf = top["confidence"]
        uncertainty = "low" if conf >= 0.75 else "medium" if conf >= 0.5 else "high"
        pred = {
            "id": new_uuid(), "hypothesis_id": top["id"], "entity_id": str(entity_id),
            "prediction_text": "Možné pokračovanie vzorca bez podpory" if conf >= 0.6 else "Neistý vývoj, potrebné ďalšie pozorovanie",
            "confidence": round(conf * 0.9, 2), "uncertainty": uncertainty,
            "alternatives": ["zlepšenie po podpore", "stagnácia", "zhoršenie"] if conf >= 0.6 else ["zlepšenie", "bez zmeny"],
            "outcome": None, "evaluated_at": None, "school_id": school_id, "created_at": utc_now(),
        }
        self.store.save_prediction(pred)
        self.store.audit("prediction.created", {"entity_id": str(entity_id), "uncertainty": uncertainty}, entity_type="entity", entity_id=str(entity_id), school_id=school_id)
        return pred
