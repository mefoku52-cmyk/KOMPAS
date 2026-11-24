from __future__ import annotations

import uuid
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.config.settings import settings
from app.integrations.sis.edupage import EduPageClientError, EduPageProvider
from app.modules.k19_sis_integration.domain.models import SISJobMode, SISJobStatus, SISSource
from app.modules.k19_sis_integration.repository.repo import SISRepository
from app.modules.k19_sis_integration.services.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.modules.k19_sis_integration.services.provisioning import SISProvisioningService
from app.shared.types import Principal, Role, utc_now


class SISService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SISRepository(db)

    def _require_leadership(self, principal: Principal, school_id: uuid.UUID):
        if principal.is_system:
            return
        if principal.role != Role.LEADERSHIP or principal.school_id != school_id:
            audit_write(self.db, principal, "sis.access", f"school:{school_id}", "sis_admin", "denied", {"reason": "leadership_required"})
            raise PermissionError("leadership_required")

    @staticmethod
    def _validate_base_url(base_url: str | None) -> None:
        if base_url is None or not base_url.strip():
            return
        parsed = urlsplit(base_url.strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        if (parsed.scheme != "https" or not host.endswith(".edupage.org")
                or parsed.username or parsed.password or parsed.port
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
            raise ValueError("invalid_edupage_base_url")

    def create_source(self, principal: Principal, *, school_id: uuid.UUID, provider_type: str, name: str, subdomain: str | None = None, base_url: str | None = None, api_key: str | None = None, config: dict | None = None, is_enabled: bool = False) -> SISSource:
        self._require_leadership(principal, school_id)
        provider_type = (provider_type or "edupage").lower().strip()
        if provider_type != "edupage":
            raise ValueError("unsupported_provider")
        self._validate_base_url(base_url)
        cfg = dict(config or {})
        if subdomain:
            cfg["subdomain"] = subdomain.strip()
        encrypted = encrypt_secret(api_key) if api_key else None
        src = self.repo.create_source(school_id=school_id, provider_type=provider_type, name=name.strip(), base_url=base_url, config=cfg, encrypted_secret=encrypted, is_enabled=is_enabled)
        audit_write(self.db, principal, "sis.source.create", f"sis_source:{src.id}", "sis_admin", "success", {"provider": provider_type, "name": name, "has_secret": bool(api_key)})
        return src

    def update_source(self, principal: Principal, *, school_id: uuid.UUID, source_id: uuid.UUID, name: str | None = None, subdomain: str | None = None, base_url: str | None = None, api_key: str | None = None, config: dict | None = None, is_enabled: bool | None = None) -> SISSource:
        self._require_leadership(principal, school_id)
        src = self.repo.get_source_for_school(school_id, source_id)
        if not src:
            raise ValueError("source_not_found")
        if name is not None:
            src.name = name.strip()
        if base_url is not None:
            self._validate_base_url(base_url)
            src.base_url = base_url
        if config is not None:
            merged = dict(src.config or {})
            merged.update(config)
            src.config = merged
        if subdomain is not None:
            merged = dict(src.config or {})
            merged["subdomain"] = subdomain.strip()
            src.config = merged
        if api_key:
            src.encrypted_secret = encrypt_secret(api_key)
        if is_enabled is not None:
            src.is_enabled = bool(is_enabled)
        self.db.flush()
        audit_write(self.db, principal, "sis.source.update", f"sis_source:{src.id}", "sis_admin", "success", {"is_enabled": src.is_enabled})
        return src

    def list_sources(self, principal: Principal, *, school_id: uuid.UUID):
        self._require_leadership(principal, school_id)
        items = self.repo.list_sources(school_id)
        return [self._source_public(s) for s in items]

    def _source_public(self, s: SISSource) -> dict:
        secret = None
        try:
            secret = decrypt_secret(s.encrypted_secret) if s.encrypted_secret else None
        except Exception:
            secret = None
        return {
            "id": str(s.id),
            "school_id": str(s.school_id),
            "provider_type": s.provider_type,
            "name": s.name,
            "base_url": s.base_url,
            "config": s.config or {},
            "is_enabled": s.is_enabled,
            "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
            "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
            "has_secret": bool(s.encrypted_secret),
            "secret_masked": mask_secret(secret),
        }

    def _provider_for_source(self, source: SISSource):
        if source.provider_type != "edupage":
            raise ValueError("unsupported_provider")
        if not source.encrypted_secret:
            raise ValueError("missing_api_key")
        api_key = decrypt_secret(source.encrypted_secret)
        subdomain = str((source.config or {}).get("subdomain") or "").strip()
        if not subdomain and source.base_url:
            parsed = urlsplit(source.base_url)
            host = (parsed.hostname or "").lower().rstrip(".")
            if not host.endswith(".edupage.org"):
                raise ValueError("invalid_edupage_base_url")
            subdomain = host.removesuffix(".edupage.org")
        if not subdomain:
            raise ValueError("missing_subdomain")
        return EduPageProvider(subdomain=subdomain, api_key=api_key, base_url=source.base_url)

    def test_connection(self, principal: Principal, *, school_id: uuid.UUID, source_id: uuid.UUID) -> dict:
        self._require_leadership(principal, school_id)
        src = self.repo.get_source_for_school(school_id, source_id)
        if not src:
            raise ValueError("source_not_found")
        try:
            provider = self._provider_for_source(src)
            result = provider.healthcheck()
            audit_write(self.db, principal, "sis.source.test", f"sis_source:{src.id}", "sis_admin", "success", {"provider": src.provider_type})
            return result
        except Exception as exc:
            audit_write(self.db, principal, "sis.source.test", f"sis_source:{src.id}", "sis_admin", "failure", {"error": str(exc)})
            raise

    def run_sync(self, principal: Principal, *, school_id: uuid.UUID, source_id: uuid.UUID, mode: str = SISJobMode.FULL.value) -> dict:
        self._require_leadership(principal, school_id)
        if mode not in {SISJobMode.FULL.value, SISJobMode.DRY_RUN.value, SISJobMode.DELTA.value}:
            raise ValueError("invalid_mode")
        if mode == SISJobMode.DELTA.value:
            mode = SISJobMode.FULL.value  # safe fallback until provider delta is confirmed
        src = self.repo.get_source_for_school(school_id, source_id)
        if not src:
            raise ValueError("source_not_found")
        if not src.is_enabled and mode != SISJobMode.DRY_RUN.value:
            raise ValueError("source_disabled")
        job = self.repo.create_job(school_id=school_id, source_id=src.id, mode=mode, status=SISJobStatus.RUNNING.value, triggered_by_user_id=principal.user_id, started_at=utc_now(), summary={})
        self.db.flush()
        audit_write(self.db, principal, "sis.sync.started", f"sis_sync_job:{job.id}", "sis_sync", "success", {"mode": mode, "source_id": str(src.id)})
        try:
            provider = self._provider_for_source(src)
            snapshot = provider.fetch_roster()
            report = SISProvisioningService(self.db).sync_roster(principal=principal, source=src, snapshot=snapshot, mode=mode)
            summary = report.as_dict()
            summary["snapshot_counts"] = {
                "school_years": len(snapshot.school_years),
                "classes": len(snapshot.classes),
                "teachers": len(snapshot.teachers),
                "students": len(snapshot.students),
                "guardians": len(snapshot.guardians),
                "enrollments": len(snapshot.enrollments),
                "class_teachers": len(snapshot.class_teachers),
                "guardian_links": len(snapshot.guardian_links),
            }
            status = SISJobStatus.SUCCESS.value if not summary["errors"] and not summary["conflicts"] else SISJobStatus.PARTIAL.value
            self.repo.update_job(job, status=status, finished_at=utc_now(), summary=summary)
            src.last_sync_at = utc_now()
            if status == SISJobStatus.SUCCESS.value and mode != SISJobMode.DRY_RUN.value:
                src.last_success_at = utc_now()
            self.db.flush()
            audit_write(self.db, principal, "sis.sync.finished", f"sis_sync_job:{job.id}", "sis_sync", "success" if status != SISJobStatus.FAILED.value else "failure", {"status": status})
            return self._job_public(job)
        except Exception as exc:
            self.repo.update_job(job, status=SISJobStatus.FAILED.value, finished_at=utc_now(), error=str(exc), summary={"error": str(exc)})
            src.last_sync_at = utc_now()
            self.db.flush()
            audit_write(self.db, principal, "sis.sync.finished", f"sis_sync_job:{job.id}", "sis_sync", "failure", {"error": str(exc)})
            raise

    def _job_public(self, job):
        return {
            "id": str(job.id),
            "school_id": str(job.school_id),
            "source_id": str(job.source_id),
            "mode": job.mode,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "summary": job.summary or {},
            "error": job.error,
        }

    def list_jobs(self, principal: Principal, *, school_id: uuid.UUID, source_id: uuid.UUID | None = None):
        self._require_leadership(principal, school_id)
        return [self._job_public(j) for j in self.repo.list_jobs(school_id, source_id=source_id)]

    def list_conflicts(self, principal: Principal, *, school_id: uuid.UUID, source_id: uuid.UUID | None = None):
        self._require_leadership(principal, school_id)
        items = self.repo.list_identities(school_id=school_id, source_id=source_id)
        conflicts = []
        for i in items:
            if i.conflict_state and i.conflict_state != "resolved":
                conflicts.append({"id": str(i.id), "entity_type": i.entity_type, "external_id": i.external_id, "internal_id": str(i.internal_id) if i.internal_id else None, "conflict_state": i.conflict_state, "conflict_detail": i.conflict_detail})
        return conflicts

    def get_job(self, principal: Principal, *, school_id: uuid.UUID, job_id: uuid.UUID):
        self._require_leadership(principal, school_id)
        job = self.repo.get_job(job_id)
        if not job or job.school_id != school_id:
            raise ValueError("job_not_found")
        return self._job_public(job)
