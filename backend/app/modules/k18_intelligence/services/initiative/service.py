from app.shared.types import utc_now, new_uuid


class InitiativeEngine:
    def __init__(self, store, safety):
        self.store = store
        self.safety = safety

    def decide(self, entity_type, entity_id, event, hypotheses, prediction, school_id=None):
        etype = event.get("event_type") if isinstance(event, dict) else getattr(event, "event_type", None)
        payload = event.get("payload", {}) if isinstance(event, dict) else getattr(event, "payload", {}) or {}
        top_conf = max([h["confidence"] for h in hypotheses], default=0)
        decision, action_type, reason, urgency, recipient_role = "observe", "observe", "nedostatočné dôkazy", "low", None

        if etype == "conflict_report" and payload.get("severity") == "high":
            decision, action_type, reason, urgency, recipient_role = "act", "notify", "vysoká závažnosť - potrebná pozornosť dospelého", "high", "teacher"
        elif etype == "minor_disagreement":
            decision, action_type, reason, urgency = "silent", "observe", "komunikácia by mohla zvýšiť napätie; vhodnejšie pozorovať", "low"
        elif etype == "teacher_note":
            decision, action_type, reason, urgency, recipient_role = "request_more", "request_more", "protichodné/čiastočné informácie - požiadať o doplnenie kontextu", "medium", "teacher"
        elif etype == "mission_answer" and payload.get("correct") is False:
            fast = float(payload.get("time_taken_sec", payload.get("time", 999)))
            recent_pattern = any("vzorec" in h.get("hypothesis_text", "").lower() or "opak" in h.get("hypothesis_text", "").lower() for h in hypotheses)
            if fast < 3 and top_conf >= 0.7 and recent_pattern:
                decision, action_type, reason, urgency, recipient_role = "act", "notify", "opakujúci sa vzorec rýchlych nesprávnych odpovedí", "medium", "teacher"
            else:
                decision, action_type, reason, urgency = "observe", "observe", "nedostatočné dôkazy na zásah", "low"
        elif top_conf < 0.4:
            decision, reason = "observe", "nízka istota - pozorovať"

        recent = self.store.list_initiatives(entity_id=str(entity_id))
        for prev in recent[:10]:
            if prev.entity_id == str(entity_id) and prev.action_type == action_type and prev.reason == reason and prev.status in ("pending", "executed", "approved"):
                self.store.audit("initiative.deduplicated", {"entity_id": str(entity_id), "reason": reason, "action_type": action_type, "previous_initiative": str(prev.id)}, entity_type=entity_type, entity_id=str(entity_id), school_id=school_id)
                return prev

        allowed, why = self.safety.can_notify(recipient_role or "teacher", action_type)
        if not allowed and decision == "act":
            decision, action_type, reason = "observe", "observe", f"bezpečnostná politika: {why}"

        init = {
            "id": new_uuid(), "situation_id": None, "entity_type": entity_type, "entity_id": str(entity_id),
            "action_type": action_type, "decision": decision, "recipient_user_id": None, "recipient_role": recipient_role,
            "status": "pending" if decision == "act" else "closed", "reason": reason, "urgency": urgency,
            "created_at": utc_now(), "decided_at": utc_now(), "decided_by": "system", "dismissed_at": None, "school_id": school_id,
        }
        rec = self.store.save_initiative(init)
        self.store.audit("initiative.decide", {"decision": decision, "reason": reason, "urgency": urgency}, entity_type=entity_type, entity_id=str(entity_id), school_id=school_id)
        return rec
