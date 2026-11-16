from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.modules.k06_virtual_lab.repository.repository import K06Repository
from app.shared.types import Principal


def _ohms_law(inputs: dict[str, Any]) -> dict[str, Any]:
    # U = R * I ; compute missing one if possible
    u = inputs.get("voltage")
    r = inputs.get("resistance")
    i = inputs.get("current")
    if u is None and r is not None and i is not None:
        u = float(r) * float(i)
    elif r is None and u is not None and i not in (None, 0):
        r = float(u) / float(i)
    elif i is None and u is not None and r not in (None, 0):
        i = float(u) / float(r)
    return {"voltage": u, "resistance": r, "current": i}


COMPUTE_REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "ohms_law": _ohms_law,
}


class K06Service:
    def __init__(self, db: Session):
        self.db = db
        self.repo = K06Repository(db)

    def _auth_school(self, principal: Principal, action: str, resource: str, school_id: uuid.UUID):
        if principal.is_system:
            return
        if principal.school_id != school_id:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": "wrong_school"})
            raise PermissionError("wrong_school")

    def ensure_sample_definition(self) -> Any:
        existing = self.repo.get_definition_by_key("sample.ohms_law")
        if existing:
            return existing
        schema = json.dumps({"inputs": {"voltage": "number?", "resistance": "number?", "current": "number?"}, "note": "provide any two"})
        obj = self.repo.create_definition(
            school_id=None,
            key="sample.ohms_law",
            name="Ohmov zakon (vzorka)",
            description="Deterministický výpočet U, R, I",
            param_schema=schema,
            compute_key="ohms_law",
            is_active=True,
            is_demo=True,
        )
        return obj

    def list_definitions(self, principal: Principal, *, school_id: uuid.UUID):
        action = "k06.list_definitions"
        resource = f"learning_simulation_definition:school:{school_id}"
        self._auth_school(principal, action, resource, school_id)
        self.ensure_sample_definition()
        rows = self.repo.list_definitions(school_id=school_id, active_only=True)
        audit_write(self.db, principal, action, resource, None, "success", {"count": len(rows)})
        return rows

    def run_simulation(self, principal: Principal, *, school_id: uuid.UUID, definition_id: uuid.UUID, inputs: dict[str, Any], is_demo: bool = False):
        action = "k06.run_simulation"
        resource = f"learning_simulation_definition:{definition_id}"
        self._auth_school(principal, action, resource, school_id)
        definition = self.repo.get_definition(definition_id)
        if not definition or not definition.is_active:
            raise ValueError("definition_not_found")
        func = COMPUTE_REGISTRY.get(definition.compute_key)
        if func is None:
            raise ValueError("compute_not_registered")
        outputs = func(inputs)
        run = self.repo.create_run(
            school_id=school_id,
            definition_id=definition.id,
            user_id=principal.user_id,
            inputs=json.dumps(inputs, sort_keys=True),
            outputs=json.dumps(outputs, sort_keys=True),
            is_demo=is_demo,
        )
        audit_write(self.db, principal, action, f"learning_simulation_run:{run.id}", None, "success")
        return run, outputs
