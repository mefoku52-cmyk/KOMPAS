import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import ValidityMixin, new_uuid


class AnalyticsAggregateSnapshot(Base, ValidityMixin):
    __tablename__ = "progress_analytics_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("school_school.id"), nullable=False, index=True)
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    group_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    group_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suppressed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0/1 for portability
    value_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
