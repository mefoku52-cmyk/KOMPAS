from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ExternalPerson:
    external_id: str
    full_name: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    username_hint: str | None = None
    is_active: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalClass:
    external_id: str
    name: str
    grade: int | None = None
    school_year_external_id: str | None = None
    is_active: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalEnrollment:
    student_external_id: str
    class_external_id: str
    school_year_external_id: str | None = None
    is_active: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalClassTeacher:
    teacher_external_id: str
    class_external_id: str
    school_year_external_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalGuardianLink:
    guardian_external_id: str
    child_student_external_id: str
    relationship: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalSchoolYear:
    external_id: str
    name: str
    is_active: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RosterSnapshot:
    school_years: list[ExternalSchoolYear] = field(default_factory=list)
    classes: list[ExternalClass] = field(default_factory=list)
    teachers: list[ExternalPerson] = field(default_factory=list)
    students: list[ExternalPerson] = field(default_factory=list)
    guardians: list[ExternalPerson] = field(default_factory=list)
    enrollments: list[ExternalEnrollment] = field(default_factory=list)
    class_teachers: list[ExternalClassTeacher] = field(default_factory=list)
    guardian_links: list[ExternalGuardianLink] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SISProvider(Protocol):
    provider_type: str

    def healthcheck(self) -> dict[str, Any]: ...

    def fetch_roster(self) -> RosterSnapshot: ...
