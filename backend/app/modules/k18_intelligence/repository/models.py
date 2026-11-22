import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.session import Base
from app.shared.types import new_uuid, utc_now


class ILPerceptionEvent(Base):
    __tablename__ = "il_perception_event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ILContextMemory(Base):
    __tablename__ = "il_context_memory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    context_type: Mapped[str] = mapped_column(String(64), nullable=False)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    source_record_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ILHypothesis(Base):
    __tablename__ = "il_hypothesis"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    situation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    hypothesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict | list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)


class ILPrediction(Base):
    __tablename__ = "il_prediction"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    hypothesis_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    prediction_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[str] = mapped_column(String(16), nullable=False)
    alternatives: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    outcome: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ILInitiative(Base):
    __tablename__ = "il_initiative"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    situation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    recipient_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)


class ILCommunication(Base):
    __tablename__ = "il_communication"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    initiative_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    content_key: Mapped[str] = mapped_column(String(128), nullable=False)
    locale: Mapped[str] = mapped_column(String(8), nullable=False, default="sk")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)


class ILOutcome(Base):
    __tablename__ = "il_outcome"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    initiative_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    feedback_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)


class ILAudit(Base):
    __tablename__ = "il_audit"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)


class ILDeadLetter(Base):
    __tablename__ = "il_dead_letter"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    handler: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
