import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum
from app.core.database.session import Base


class BehavioralState(str, enum.Enum):
    """Odvodené, neutrálne stavy založené na pozorovateľných udalostiach."""
    NEUTRAL = "neutral"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    AVOIDANCE = "avoidance"
    FLOW = "flow"


class WellbeingObservation(Base):
    __tablename__ = "k17_wellbeing_observations"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)
    inferred_state = Column(SQLEnum(BehavioralState), nullable=False, default=BehavioralState.NEUTRAL)
    alert_level = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
