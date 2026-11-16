from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.modules.k16_intelligent_core.rule_system.service import RuleSystemService
from app.shared.types import Principal


class ModelProvider(Protocol):
    name: str

    def generate(self, prompt: str, *, task: str, context: Optional[dict[str, Any]] = None) -> str: ...


@dataclass
class NullProvider:
    name: str = "null"

    def generate(self, prompt: str, *, task: str, context: Optional[dict[str, Any]] = None) -> str:
        # deterministic, no network, no external data
        return f"[null:{task}]"


class OrchestratorService:
    def __init__(self, db: Session, providers: Optional[dict[str, ModelProvider]] = None, rule_system: Optional[RuleSystemService] = None):
        self.db = db
        self.providers = providers or {"null": NullProvider()}
        self.rule_system = rule_system or RuleSystemService()

    def select_provider(self, task: str) -> ModelProvider:
        # simple deterministic selection; extensible via config/providers map
        if task in self.providers:
            return self.providers[task]
        return self.providers.get("null") or NullProvider()

    def run(self, principal: Principal, task: str, prompt: str, payload: Optional[dict[str, Any]] = None, context: Optional[dict[str, Any]] = None) -> str:
        payload = payload or {}
        ctx = context or {}
        requested_fields = payload.keys() if payload else None
        decision = self.rule_system.evaluate(principal, action=f"ai.{task}", requested_fields=requested_fields, context=ctx, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, "ai.orchestrator.call", f"task:{task}", ctx.get("purpose"), "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)
        provider = self.select_provider(task)
        safe_payload = self.rule_system.filter_payload(payload)
        output = provider.generate(prompt, task=task, context=safe_payload)
        audit_write(
            self.db,
            principal,
            "ai.orchestrator.call",
            f"task:{task}",
            ctx.get("purpose"),
            "success",
            {"provider": getattr(provider, "name", "unknown"), "prompt_len": len(prompt)},
        )
        return output
