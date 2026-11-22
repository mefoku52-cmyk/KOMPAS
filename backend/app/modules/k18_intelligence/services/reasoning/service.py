from app.shared.types import utc_now, new_uuid


class ReasoningEngine:
    def __init__(self, store):
        self.store = store

    def evaluate(self, entity_type, entity_id, event, context, school_id=None):
        etype = event.get("event_type") if isinstance(event, dict) else getattr(event, "event_type", None)
        payload = event.get("payload", {}) if isinstance(event, dict) else getattr(event, "payload", {}) or {}
        event_id = event.get("event_id") if isinstance(event, dict) else getattr(event, "event_id", None)
        hyps = []
        base_evidence = [{"event_id": str(event_id) if event_id else None, "type": etype, "payload": payload}]

        if etype == "mission_answer" and payload.get("correct") is False:
            fast = float(payload.get("time_taken_sec", payload.get("time", 999)))
            recent_incorrect = [c for c in context if getattr(c, "context_type", None) == "signal" and (getattr(c, "context", {}) or {}).get("correct") is False]
            prior_incorrect = max(0, len(recent_incorrect) - 1)
            if fast < 3 and prior_incorrect >= 1:
                hyps.append(self._hyp(entity_type, entity_id, "Možný vzorec unáhleného odpovedania alebo frustrácie", 0.72, base_evidence + [{"history_count": prior_incorrect + 1}], school_id))
                hyps.append(self._hyp(entity_type, entity_id, "Alternatíva: úloha je príliš náročná alebo nejasná", 0.45, base_evidence + [{"history": "difficulty"}], school_id))
            else:
                hyps.append(self._hyp(entity_type, entity_id, "Jednorazová chyba alebo nedostatok dôkazov na vzorec", 0.55, base_evidence + [{"prior_incorrect": prior_incorrect}], school_id))
                hyps.append(self._hyp(entity_type, entity_id, "Alternatíva: dočasná nepozornosť", 0.35, base_evidence, school_id))
        elif etype == "conflict_report":
            sev = payload.get("severity", "low")
            conf = 0.85 if sev == "high" else 0.6
            hyps.append(self._hyp(entity_type, entity_id, "Možný konflikt vyžadujúci pozornosť dospelého", conf, base_evidence, school_id))
            hyps.append(self._hyp(entity_type, entity_id, "Alternatíva: situácia sa môže upokojiť bez zásahu", 0.25, base_evidence, school_id))
        elif etype == "teacher_note":
            hyps.append(self._hyp(entity_type, entity_id, "Kvalitatívny signál vyžaduje overenie a kontext", 0.5, base_evidence, school_id))
            hyps.append(self._hyp(entity_type, entity_id, "Alternatíva: pozorovanie nemusí súvisieť s výkonom", 0.4, base_evidence, school_id))
        elif etype == "minor_disagreement":
            hyps.append(self._hyp(entity_type, entity_id, "Bežná situácia, kde komunikácia môže zvýšiť napätie", 0.7, base_evidence, school_id))
            hyps.append(self._hyp(entity_type, entity_id, "Alternatíva: tichá podpora môže byť vhodná", 0.4, base_evidence, school_id))
        else:
            hyps.append(self._hyp(entity_type, entity_id, "Nedostatočný kontext na spoľahlivý záver", 0.3, base_evidence, school_id))

        for h in hyps:
            self.store.save_hypothesis(h)
        self.store.audit("reasoning.hypotheses", {"entity_id": str(entity_id), "count": len(hyps)}, entity_type=entity_type, entity_id=str(entity_id), school_id=school_id)
        return hyps

    def _hyp(self, entity_type, entity_id, text, confidence, evidence, school_id):
        return {"id": new_uuid(), "situation_id": None, "entity_type": entity_type, "entity_id": str(entity_id), "hypothesis_text": text, "confidence": confidence, "evidence": evidence, "status": "active", "created_at": utc_now(), "validated_at": None, "expires_at": None, "school_id": school_id}
