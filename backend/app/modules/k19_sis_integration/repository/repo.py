from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k19_sis_integration.domain.models import (
    SISConflictState,
    SISIdentityMap,
    SISJobStatus,
    SISSource,
    SISSyncItem,
    SISSyncJob,
)


class SISRepository:
    def __init__(self, db: Session):
        self.db = db

    # sources
    def list_sources(self, school_id: uuid.UUID) -> list[SISSource]:
        return list(self.db.execute(select(SISSource).where(SISSource.school_id == school_id).order_by(SISSource.valid_from.desc())).scalars().all())

    def get_source(self, source_id: uuid.UUID) -> SISSource | None:
        return self.db.get(SISSource, source_id)

    def get_source_for_school(self, school_id: uuid.UUID, source_id: uuid.UUID) -> SISSource | None:
        return self.db.execute(select(SISSource).where(SISSource.id == source_id, SISSource.school_id == school_id)).scalar_one_or_none()

    def create_source(self, **kwargs) -> SISSource:
        obj = SISSource(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    # identity map
    def get_identity(self, *, source_id: uuid.UUID, entity_type: str, external_id: str) -> SISIdentityMap | None:
        return self.db.execute(
            select(SISIdentityMap).where(
                SISIdentityMap.source_id == source_id,
                SISIdentityMap.entity_type == entity_type,
                SISIdentityMap.external_id == str(external_id),
            )
        ).scalar_one_or_none()

    def upsert_identity(self, *, school_id, source_id, provider_type, entity_type, external_id, internal_id=None, external_key=None, payload_hash=None, conflict_state=SISConflictState.RESOLVED.value, conflict_detail=None, seen_at: datetime | None = None, absent_runs: int | None = None) -> SISIdentityMap:
        obj = self.get_identity(source_id=source_id, entity_type=entity_type, external_id=str(external_id))
        if obj is None:
            obj = SISIdentityMap(
                school_id=school_id, source_id=source_id, provider_type=provider_type,
                entity_type=entity_type, external_id=str(external_id), internal_id=internal_id,
                external_key=external_key, payload_hash=payload_hash, last_seen_at=seen_at,
                absent_runs=0 if absent_runs is None else absent_runs,
                conflict_state=conflict_state, conflict_detail=conflict_detail,
            )
            self.db.add(obj)
        else:
            if internal_id is not None:
                obj.internal_id = internal_id
            obj.external_key = external_key
            obj.payload_hash = payload_hash
            obj.last_seen_at = seen_at
            if absent_runs is not None:
                obj.absent_runs = absent_runs
            obj.conflict_state = conflict_state
            obj.conflict_detail = conflict_detail
        self.db.flush()
        return obj

    def list_identities(self, *, school_id: uuid.UUID, source_id: uuid.UUID | None = None, entity_type: str | None = None) -> list[SISIdentityMap]:
        stmt = select(SISIdentityMap).where(SISIdentityMap.school_id == school_id)
        if source_id:
            stmt = stmt.where(SISIdentityMap.source_id == source_id)
        if entity_type:
            stmt = stmt.where(SISIdentityMap.entity_type == entity_type)
        return list(self.db.execute(stmt.order_by(SISIdentityMap.entity_type.asc(), SISIdentityMap.external_id.asc())).scalars().all())

    # jobs
    def create_job(self, **kwargs) -> SISSyncJob:
        obj = SISSyncJob(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_job(self, job: SISSyncJob, **kwargs) -> SISSyncJob:
        for k, v in kwargs.items():
            setattr(job, k, v)
        self.db.flush()
        return job

    def add_item(self, **kwargs) -> SISSyncItem:
        obj = SISSyncItem(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_jobs(self, school_id: uuid.UUID, source_id: uuid.UUID | None = None, limit: int = 50) -> list[SISSyncJob]:
        stmt = select(SISSyncJob).where(SISSyncJob.school_id == school_id)
        if source_id:
            stmt = stmt.where(SISSyncJob.source_id == source_id)
        return list(self.db.execute(stmt.order_by(SISSyncJob.valid_from.desc()).limit(limit)).scalars().all())

    def list_items(self, job_id: uuid.UUID, limit: int = 500) -> list[SISSyncItem]:
        return list(self.db.execute(select(SISSyncItem).where(SISSyncItem.job_id == job_id).order_by(SISSyncItem.valid_from.asc()).limit(limit)).scalars().all())

    def get_job(self, job_id: uuid.UUID) -> SISSyncJob | None:
        return self.db.get(SISSyncJob, job_id)
