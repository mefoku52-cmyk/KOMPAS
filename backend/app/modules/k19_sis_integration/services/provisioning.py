from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.config.settings import settings
from app.core.security.auth import hash_password
from app.integrations.sis.base import RosterSnapshot
from app.modules.k19_sis_integration.domain.models import (
    SISConflictState,
    SISJobMode,
    SISJobStatus,
    SISSource,
)
from app.modules.k19_sis_integration.repository.repo import SISRepository
from app.shared.identity import GuardianLink, RoleAssignment, User
from app.shared.school import ClassGroup, Enrollment, SchoolYear
from app.shared.types import Principal, Role, utc_now

try:
    from app.modules.k09_class_overview.domain.models import ClassTeacherAssignment
except Exception:  # pragma: no cover
    ClassTeacherAssignment = None  # type: ignore


@dataclass
class SyncReport:
    created: dict[str, int] = field(default_factory=dict)
    updated: dict[str, int] = field(default_factory=dict)
    unchanged: dict[str, int] = field(default_factory=dict)
    conflicts: list[dict] = field(default_factory=list)
    deactivated_candidates: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    def inc(self, bucket: str, key: str, n: int = 1):
        target = getattr(self, bucket)
        target[key] = target.get(key, 0) + n

    def as_dict(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "conflicts": self.conflicts,
            "deactivated_candidates": self.deactivated_candidates,
            "errors": self.errors,
        }


def _slug(s: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9_.-]+", "_", s.strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "user")[:max_len]


def _payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


class SISProvisioningService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SISRepository(db)

    def _audit(self, principal: Principal, action: str, resource: str, outcome: str, details: dict | None = None):
        audit_write(self.db, principal, action, resource, "sis_sync", outcome, details or {})

    def _ensure_username(self, school_id: uuid.UUID, base: str) -> str:
        base = _slug(base)
        candidate = base
        i = 1
        while self.db.execute(select(User.id).where(User.school_id == school_id, User.username == candidate)).first() is not None:
            i += 1
            suffix = f"_{i}"
            candidate = f"{base[: max(1, 48-len(suffix))]}{suffix}"
        return candidate

    def _get_or_create_year(self, school_id: uuid.UUID, name: str, *, dry_run: bool, report: SyncReport):
        obj = self.db.execute(select(SchoolYear).where(SchoolYear.school_id == school_id, SchoolYear.name == name)).scalar_one_or_none()
        if obj:
            report.inc("unchanged", "school_years")
            return obj, False
        obj = SchoolYear(school_id=school_id, name=name)
        if not dry_run:
            self.db.add(obj)
            self.db.flush()
        report.inc("created", "school_years")
        return obj, True

    def _get_or_create_class(self, school_id: uuid.UUID, year_id: uuid.UUID, name: str, grade: int | None, *, dry_run: bool, report: SyncReport):
        obj = self.db.execute(select(ClassGroup).where(ClassGroup.school_year_id == year_id, ClassGroup.name == name)).scalar_one_or_none()
        if obj:
            changed = False
            if grade is not None and obj.grade != grade:
                if not dry_run:
                    obj.grade = grade
                changed = True
            report.inc("updated" if changed else "unchanged", "classes")
            return obj, changed
        obj = ClassGroup(school_id=school_id, school_year_id=year_id, name=name, grade=grade or settings.grade_min)
        if not dry_run:
            self.db.add(obj)
            self.db.flush()
        report.inc("created", "classes")
        return obj, True

    def _ensure_role(self, user_id: uuid.UUID, school_id: uuid.UUID, role: Role, *, dry_run: bool):
        ra = self.db.execute(select(RoleAssignment).where(RoleAssignment.user_id == user_id, RoleAssignment.school_id == school_id, RoleAssignment.role == role.value)).scalar_one_or_none()
        if ra:
            return False
        if not dry_run:
            self.db.add(RoleAssignment(user_id=user_id, school_id=school_id, role=role.value))
            self.db.flush()
        return True

    def _upsert_person(self, *, principal: Principal, source: SISSource, ext, role: Role, report: SyncReport, dry_run: bool, seen_at: datetime):
        entity_type = "teacher" if role == Role.TEACHER else "student" if role == Role.STUDENT else "guardian"
        ph = _payload_hash(ext.raw or {"id": ext.external_id, "name": ext.full_name, "active": ext.is_active})
        ident = self.repo.get_identity(source_id=source.id, entity_type=entity_type, external_id=ext.external_id)
        user = self.db.get(User, ident.internal_id) if ident and ident.internal_id else None
        if user is None:
            base = ext.username_hint or f"{source.provider_type[:2]}_{entity_type[0]}_{ext.external_id}"
            username = self._ensure_username(source.school_id, base)
            user = User(school_id=source.school_id, username=username, full_name=ext.full_name, password_hash=hash_password(uuid.uuid4().hex), is_active=bool(ext.is_active))
            if not dry_run:
                self.db.add(user)
                self.db.flush()
                self._ensure_role(user.id, source.school_id, role, dry_run=False)
            report.inc("created", f"{entity_type}s")
            self._audit(principal, "sis.user.created", f"identity_user:{user.id}", "success", {"source": source.provider_type, "entity_type": entity_type, "external_id": ext.external_id})
        else:
            changed = False
            if user.full_name != ext.full_name:
                if not dry_run:
                    user.full_name = ext.full_name
                changed = True
            if user.is_active != bool(ext.is_active):
                if not dry_run:
                    user.is_active = bool(ext.is_active)
                changed = True
            self._ensure_role(user.id, source.school_id, role, dry_run=dry_run)
            report.inc("updated" if changed else "unchanged", f"{entity_type}s")
        self.repo.upsert_identity(school_id=source.school_id, source_id=source.id, provider_type=source.provider_type, entity_type=entity_type, external_id=ext.external_id, internal_id=user.id, external_key=ext.email or ext.username_hint, payload_hash=ph, conflict_state=SISConflictState.RESOLVED.value, conflict_detail=None, seen_at=seen_at, absent_runs=0)
        return user

    def sync_roster(self, *, principal: Principal, source: SISSource, snapshot: RosterSnapshot, mode: str = SISJobMode.FULL.value) -> SyncReport:
        dry_run = mode == SISJobMode.DRY_RUN.value
        seen_at = utc_now()
        report = SyncReport()

        year_by_ext: dict[str, uuid.UUID] = {}
        # default year: newest active or first
        default_year = self.db.execute(select(SchoolYear).where(SchoolYear.school_id == source.school_id).order_by(SchoolYear.valid_from.desc())).scalars().first()
        if default_year is None:
            default_year, _ = self._get_or_create_year(source.school_id, f"{datetime.now().year}/{datetime.now().year+1}", dry_run=dry_run, report=report)
        for y in snapshot.school_years:
            obj, _ = self._get_or_create_year(source.school_id, y.name, dry_run=dry_run, report=report)
            if obj.id:
                year_by_ext[y.external_id] = obj.id

        class_by_ext: dict[str, ClassGroup] = {}
        for c in snapshot.classes:
            year_id = year_by_ext.get(c.school_year_external_id or "", default_year.id)
            obj, _ = self._get_or_create_class(source.school_id, year_id, c.name, c.grade, dry_run=dry_run, report=report)
            self.repo.upsert_identity(school_id=source.school_id, source_id=source.id, provider_type=source.provider_type, entity_type="class", external_id=c.external_id, internal_id=obj.id, external_key=c.name, payload_hash=_payload_hash(c.raw), conflict_state=SISConflictState.RESOLVED.value, seen_at=seen_at)
            class_by_ext[c.external_id] = obj

        teacher_by_ext: dict[str, User] = {}
        for t in snapshot.teachers:
            user = self._upsert_person(principal=principal, source=source, ext=t, role=Role.TEACHER, report=report, dry_run=dry_run, seen_at=seen_at)
            teacher_by_ext[t.external_id] = user

        student_by_ext: dict[str, User] = {}
        for s in snapshot.students:
            user = self._upsert_person(principal=principal, source=source, ext=s, role=Role.STUDENT, report=report, dry_run=dry_run, seen_at=seen_at)
            student_by_ext[s.external_id] = user

        guardian_by_ext: dict[str, User] = {}
        for g in snapshot.guardians:
            user = self._upsert_person(principal=principal, source=source, ext=g, role=Role.PARENT, report=report, dry_run=dry_run, seen_at=seen_at)
            guardian_by_ext[g.external_id] = user

        # enrollments
        for e in snapshot.enrollments:
            student = student_by_ext.get(e.student_external_id)
            cls = class_by_ext.get(e.class_external_id)
            if not student or not cls:
                report.conflicts.append({"type": "enrollment_missing_ref", "student": e.student_external_id, "class": e.class_external_id})
                continue
            year_id = cls.school_year_id
            existing = self.db.execute(select(Enrollment).where(Enrollment.school_year_id == year_id, Enrollment.student_user_id == student.id)).scalar_one_or_none()
            if existing:
                if existing.class_group_id != cls.id:
                    if not dry_run:
                        existing.class_group_id = cls.id
                    report.inc("updated", "enrollments")
                    self._audit(principal, "sis.enrollment.changed", f"school_enrollment:{existing.id}", "success", {"student_user_id": str(student.id), "class_group_id": str(cls.id), "external_student": e.student_external_id})
                else:
                    report.inc("unchanged", "enrollments")
            else:
                if not dry_run:
                    self.db.add(Enrollment(school_id=source.school_id, school_year_id=year_id, class_group_id=cls.id, student_user_id=student.id))
                    self.db.flush()
                report.inc("created", "enrollments")
        # class teachers
        if ClassTeacherAssignment is not None:
            for ct in snapshot.class_teachers:
                teacher = teacher_by_ext.get(ct.teacher_external_id)
                cls = class_by_ext.get(ct.class_external_id)
                if not teacher or not cls:
                    report.conflicts.append({"type": "class_teacher_missing_ref", "teacher": ct.teacher_external_id, "class": ct.class_external_id})
                    continue
                exists = self.db.execute(select(ClassTeacherAssignment).where(ClassTeacherAssignment.school_id == source.school_id, ClassTeacherAssignment.class_group_id == cls.id, ClassTeacherAssignment.teacher_user_id == teacher.id)).scalar_one_or_none()
                if exists:
                    report.inc("unchanged", "class_teachers")
                else:
                    if not dry_run:
                        self.db.add(ClassTeacherAssignment(school_id=source.school_id, class_group_id=cls.id, teacher_user_id=teacher.id))
                        self.db.flush()
                    report.inc("created", "class_teachers")

        # guardians
        for gl in snapshot.guardian_links:
            guardian = guardian_by_ext.get(gl.guardian_external_id)
            child = student_by_ext.get(gl.child_student_external_id)
            if not guardian or not child:
                report.conflicts.append({"type": "guardian_link_missing_ref", "guardian": gl.guardian_external_id, "child": gl.child_student_external_id})
                continue
            exists = self.db.execute(select(GuardianLink).where(GuardianLink.school_id == source.school_id, GuardianLink.guardian_user_id == guardian.id, GuardianLink.child_user_id == child.id)).scalar_one_or_none()
            if exists:
                report.inc("unchanged", "guardian_links")
            else:
                if not dry_run:
                    self.db.add(GuardianLink(school_id=source.school_id, guardian_user_id=guardian.id, child_user_id=child.id, relationship=gl.relationship))
                    self.db.flush()
                report.inc("created", "guardian_links")

        # absent entities: report candidates; optional safe auto-deactivate
        for ident in self.repo.list_identities(school_id=source.school_id, source_id=source.id):
            if ident.entity_type not in {"student", "teacher", "guardian"}:
                continue
            last_seen = ident.last_seen_at
            if last_seen and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen and last_seen >= seen_at:
                continue
            absent_runs = int(getattr(ident, "absent_runs", 0) or 0) + 1
            if not dry_run:
                ident.absent_runs = absent_runs
            deactivated = False
            threshold = max(1, int(settings.sis_deactivate_absent_after_runs))
            if settings.sis_auto_deactivate_enabled and absent_runs >= threshold and ident.internal_id:
                user = self.db.get(User, ident.internal_id)
                if user and user.is_active:
                    if not dry_run:
                        user.is_active = False
                    deactivated = True
                    report.inc("updated", f"{ident.entity_type}s")
                    self._audit(principal, "sis.user.deactivated_absent", f"identity_user:{user.id}", "success", {"entity_type": ident.entity_type, "external_id": ident.external_id, "absent_runs": absent_runs})
            report.deactivated_candidates.append({
                "entity_type": ident.entity_type,
                "external_id": ident.external_id,
                "internal_id": str(ident.internal_id) if ident.internal_id else None,
                "absent_runs": absent_runs,
                "deactivated": deactivated,
            })
        self._audit(principal, "sis.sync.completed", f"sis_source:{source.id}", "success", {"mode": mode, "summary": report.as_dict()})
        return report
