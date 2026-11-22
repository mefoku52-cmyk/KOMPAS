from app.modules.k18_intelligence.config import SETTINGS
from app.modules.k18_intelligence.repository.models import ILCommunication, ILInitiative
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone


class SafetyGovernance:
    FORBIDDEN_TERMS = ["hlúpy", "problémový žiak", "zlý", "neschopný", "skóre žiaka"]

    def check_communication(self, text, role):
        lowered = (text or "").lower()
        for t in self.FORBIDDEN_TERMS:
            if t in lowered:
                return False, f"forbidden_term:{t}"
        if role in ("student", "parent") and "skóre" in lowered:
            return False, "score_forbidden_for_role"
        return True, "ok"

    def can_notify(self, role, action_type):
        if not SETTINGS["INTELLIGENCE_ENABLED"]:
            return False, "intelligence_disabled"
        if action_type == "notify" and role not in ("teacher", "leadership", "specialist", "parent", "student"):
            return False, "unknown_role"
        return True, "ok"

    def rate_limit_allows(self, db, entity_id, recipient_role):
        if not entity_id or not recipient_role:
            return True, "ok"
        since = datetime.now(timezone.utc) - timedelta(days=1)
        stmt = select(func.count(ILCommunication.id)).join(ILInitiative, ILCommunication.initiative_id == ILInitiative.id).where(
            ILInitiative.entity_id == str(entity_id),
            ILInitiative.recipient_role == recipient_role,
            ILCommunication.sent_at >= since,
        )
        count = db.execute(stmt).scalar() or 0
        limit = SETTINGS.get("MAX_NOTIFICATIONS_PER_ENTITY_PER_DAY", 3)
        if count >= limit:
            return False, f"rate_limited:{count}>={limit}"
        return True, "ok"

    def requires_human_approval(self, urgency, entity_type):
        return bool(SETTINGS["HUMAN_APPROVAL_REQUIRED_FOR_SENSITIVE"] and urgency == "high" and entity_type == "student")
