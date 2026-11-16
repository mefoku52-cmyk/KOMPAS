from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Role(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    LEADERSHIP = "leadership"
    PARENT = "parent"


SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    role: Optional[Role] = None
    school_id: Optional[uuid.UUID] = None
    scopes: tuple[str, ...] = field(default_factory=tuple)
    is_system: bool = False


def system_principal() -> Principal:
    return Principal(user_id=SYSTEM_USER_ID, role=None, school_id=None, scopes=("system",), is_system=True)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ValidityMixin:
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
