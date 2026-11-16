from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k06_virtual_lab.domain.models import SimulationDefinition, SimulationRun


class K06Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_definition(self, *, school_id: uuid.UUID | None, key: str, name: str, description: str | None, param_schema: str | None, compute_key: str, is_active: bool = True, is_demo: bool = False) -> SimulationDefinition:
        obj = SimulationDefinition(school_id=school_id, key=key, name=name, description=description, param_schema=param_schema, compute_key=compute_key, is_active=is_active, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_definition(self, definition_id: uuid.UUID) -> SimulationDefinition | None:
        return self.db.get(SimulationDefinition, definition_id)

    def get_definition_by_key(self, key: str) -> SimulationDefinition | None:
        stmt = select(SimulationDefinition).where(SimulationDefinition.key == key)
        return self.db.execute(stmt).scalars().first()

    def list_definitions(self, school_id: uuid.UUID | None = None, active_only: bool = True) -> list[SimulationDefinition]:
        stmt = select(SimulationDefinition)
        if school_id is not None:
            stmt = stmt.where((SimulationDefinition.school_id == school_id) | (SimulationDefinition.school_id.is_(None)))
        if active_only:
            stmt = stmt.where(SimulationDefinition.is_active.is_(True))
        return list(self.db.execute(stmt).scalars().all())

    def create_run(self, *, school_id: uuid.UUID, definition_id: uuid.UUID, user_id: uuid.UUID, inputs: str, outputs: str, is_demo: bool = False) -> SimulationRun:
        obj = SimulationRun(school_id=school_id, definition_id=definition_id, user_id=user_id, inputs=inputs, outputs=outputs, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_runs(self, definition_id: uuid.UUID, user_id: uuid.UUID | None = None) -> list[SimulationRun]:
        stmt = select(SimulationRun).where(SimulationRun.definition_id == definition_id)
        if user_id is not None:
            stmt = stmt.where(SimulationRun.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())
