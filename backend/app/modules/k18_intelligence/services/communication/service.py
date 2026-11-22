from app.shared.types import utc_now, new_uuid

TEMPLATES = {
    "teacher.signal.support": {
        "sk": "KOMPAS zaznamenal opakujúci sa vzorec, ktorý môže naznačovať potrebu podpory. Odporúčame pokojne skontrolovať kontext a ponúknuť pomoc.",
        "en": "KOMPAS noticed a recurring pattern that may indicate a need for support. Consider calmly checking context and offering help.",
    },
    "teacher.signal.urgent": {
        "sk": "KOMPAS zaznamenal situáciu s vyššou naliehavosťou. Odporúčame venovať jej pozornosť a overiť kontext.",
        "en": "KOMPAS noticed a higher-urgency situation. Consider reviewing the context.",
    },
    "teacher.request_more": {
        "sk": "KOMPAS má neúplné informácie. Ak je to možné, doplňte kontext pred zásahom.",
        "en": "KOMPAS has incomplete information. If possible, add context before acting.",
    },
    "student.neutral.support": {
        "sk": "Ak chceš, môžeš si urobiť krátku prestávku alebo skúsiť úlohu iným tempom. Pomoc je k dispozícii.",
        "en": "If you want, you can take a short break or try a different pace. Help is available.",
    },
    "parent.neutral.support": {
        "sk": "KOMPAS zaznamenal moment, kde môže byť užitočná pokojná podpora. Ak chcete, môžete sa opýtať, ako dieťaťu ide učenie.",
        "en": "KOMPAS noticed a moment where calm support may help. If you wish, you can ask how learning is going.",
    },
}


class CommunicationEngine:
    def __init__(self, store, safety, db):
        self.store = store
        self.safety = safety
        self.db = db

    def _template_key(self, initiative):
        if initiative.action_type == "request_more":
            return "teacher.request_more"
        if initiative.recipient_role == "student":
            return "student.neutral.support"
        if initiative.recipient_role == "parent":
            return "parent.neutral.support"
        return "teacher.signal.urgent" if initiative.urgency == "high" else "teacher.signal.support"

    def compose_and_send(self, initiative, locale="sk"):
        if initiative.decision != "act" and initiative.action_type != "request_more":
            return None
        role = initiative.recipient_role or "teacher"
        allowed, why = self.safety.rate_limit_allows(self.db, initiative.entity_id, role)
        if not allowed:
            self.store.audit("communication.rate_limited", {"reason": why, "initiative_id": str(initiative.id)}, entity_type="initiative", entity_id=str(initiative.id), school_id=initiative.school_id)
            return None
        key = self._template_key(initiative)
        text = TEMPLATES.get(key, {}).get(locale) or TEMPLATES.get(key, {}).get("sk")
        ok, why = self.safety.check_communication(text, role)
        if not ok:
            self.store.audit("communication.blocked", {"reason": why, "initiative_id": str(initiative.id)}, entity_type="initiative", entity_id=str(initiative.id), school_id=initiative.school_id)
            return None
        comm = {
            "id": new_uuid(), "initiative_id": initiative.id, "channel": "in_app", "content_key": key,
            "locale": locale, "payload": {"text": text, "entity_id": initiative.entity_id, "reason": initiative.reason},
            "status": "delivered", "sent_at": utc_now(), "acknowledged_at": None, "school_id": initiative.school_id,
        }
        rec = self.store.save_communication(comm)
        self.store.update_initiative_status(initiative.id, "executed", actor="system")
        self.store.audit("communication.sent", {"communication_id": str(rec.id), "content_key": key}, entity_type="communication", entity_id=str(rec.id), school_id=initiative.school_id)
        return rec
