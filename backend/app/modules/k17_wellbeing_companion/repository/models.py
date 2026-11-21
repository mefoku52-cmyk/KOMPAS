import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BehavioralState(str, enum.Enum):
    """
    Psychologický koncept: Stav je odvodený výlučne z dát, nie z emócií.
    - NEUTRAL: Bazálna línia žiaka je zachovaná.
    - COGNITIVE_OVERLOAD: Prudký nárast času na úlohu + chyby (frustrácia/zmätenie).
    - AVOIDANCE: Dlhá pauza po úspechu alebo séria rýchlych, náhodných odpovedí (únik).
    - FLOW: Optimálne tempo, vysoká úspešnosť, žiadne váhanie.
    """
    NEUTRAL = "neutral"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    AVOIDANCE = "avoidance"
    FLOW = "flow"

class WellbeingObservation(Base):
    __tablename__ = "k17_wellbeing_observations"

    id = Column(String(36), primary_key=True) # UUID
    student_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # Čo sa stalo (fakt)
    event_type = Column(String(50), nullable=False) # napr. "mission_answer", "page_idle"
    
    # Metriky (dáta pre "mentalistu")
    metrics = Column(JSON, nullable=False, default=dict) 
    # Príklad metrics: {"time_taken_sec": 45.2, "consecutive_errors": 2, "hints_used": 1}
    
    # Odvodený stav (výpočet service vrstvy)
    inferred_state = Column(SQLEnum(BehavioralState), nullable=False, default=BehavioralState.NEUTRAL)
    alert_level = Column(Integer, nullable=False, default=0) # 0 = OK, 1 = Monitor, 2 = Intervene
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
