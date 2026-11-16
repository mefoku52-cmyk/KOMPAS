from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from app.core.permissions.policy import authorize as core_authorize
from app.shared.types import Principal


FORBIDDEN_AI_ACTIONS = {
    "pedagogical_decision",
    "personality_assessment",
    "behavioral_inference",
    "automatic_grading_of_personality",
}


@dataclass
class RuleDecision:
    allowed: bool
    reason: str


class RuleSystemService:
    def __init__(self, allowed_fields: Optional[Iterable[str]] = None):
        self.allowed_fields = set(allowed_fields or {
            "topic_id",
            "topic_name",
            "subject_id",
            "attempt_result",
            "score",
            "status",
            "grade",
            "recommendation_reason",
            "school_id",
            "class_group_id",
        })

    def evaluate(
        self,
        principal: Principal,
        action: str,
        requested_fields: Optional[Iterable[str]] = None,
        context: Optional[dict[str, Any]] = None,
        db=None,
    ) -> RuleDecision:
        normalized = action.removeprefix("ai.")
        if action in FORBIDDEN_AI_ACTIONS or normalized in FORBIDDEN_AI_ACTIONS:
            return RuleDecision(False, "forbidden_ai_action")
        # rule_system uses core/permissions
        perm = core_authorize(principal, action, resource="ai", context=context or {}, db=db)
        if not perm.allowed:
            return RuleDecision(False, f"permission_denied:{perm.reason}")
        if requested_fields is not None:
            bad = [f for f in requested_fields if f not in self.allowed_fields]
            if bad:
                return RuleDecision(False, "disallowed_fields")
        return RuleDecision(True, "allowed")

    def filter_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in payload.items() if k in self.allowed_fields}
