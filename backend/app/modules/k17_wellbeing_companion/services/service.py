from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

# Opravený import: začíname priamo od 'app'
from app.modules.k17_wellbeing_companion.repository.models import (
    WellbeingObservation, BehavioralState
)

class WellbeingAnalyticService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def record_observation(self, student_id: str, event_type: str, metrics: Dict[str, Any]) -> WellbeingObservation:
        """
        Zaznamená surové dáta a vypočíta aktuálny stav na základe kontextu.
        """
        # 1. Získaj posledných 5 pozorovaní tohto žiaka pre kontext (bazálna línia)
        recent_obs = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id
        ).order_by(WellbeingObservation.timestamp.desc()).limit(5).all()
        
        # 2. Analyzuj vzorec (Patrick Jane prístup: hľadaj nezrovnalosti v dátach)
        state, alert_level = self._analyze_pattern(metrics, recent_obs)

        # 3. Vytvor a ulož záznam
        observation = WellbeingObservation(
            id=str(uuid.uuid4()),
            student_id=student_id,
            event_type=event_type,
            metrics=metrics,
            inferred_state=state,
            alert_level=alert_level,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)
        return observation

    def _analyze_pattern(self, current_metrics: Dict[str, Any], history: List[WellbeingObservation]) -> tuple:
        """
        Detekcia stavu bez manipulácie. Iba matematika a behaviorálne vzorce.
        """
        consecutive_errors = current_metrics.get("consecutive_errors", 0)
        time_taken = current_metrics.get("time_taken_sec", 0)
        
        # Priemer času z histórie (ak existuje)
        avg_time = sum(o.metrics.get("time_taken_sec", 0) for o in history) / len(history) if history else 30.0
        
        # PRAVIDLO 1: Kognitívne preťaženie (Cognitive Overload)
        # Žiak robí chyby a čas sa predlžuje. Nie je to o inteligencii, je to o zablokovaní.
        if consecutive_errors >= 2 and time_taken > (avg_time * 1.5):
            return BehavioralState.COGNITIVE_OVERLOAD, 2
            
        # PRAVIDLO 2: Únik/Avoidance
        # Veľmi rýchla odpoveď (< 3 sekundy) po sérii chýb = náhodné klikanie a snaha mať to za sebou.
        if consecutive_errors >= 1 and time_taken < 3.0:
            return BehavioralState.AVOIDANCE, 2
            
        # PRAVIDLO 3: Flow (optimálny stav)
        # Čas je stabilný, chyby sú 0 alebo 1 (bežná korekcia).
        if consecutive_errors == 0 and (avg_time * 0.5) <= time_taken <= (avg_time * 1.2):
            return BehavioralState.FLOW, 0
            
        # Predvolený stav: Neutrálny (pokračuje v zabehnutom tempe)
        return BehavioralState.NEUTRAL, 0

    def get_intervention_prompt(self, student_id: str) -> str:
        """
        Vygeneruje text pre K-14 (Communication). 
        Pravidlo: Žiadna chvála ("Si šikovný!"), žiadny súcit ("To je ťažké, že?").
        Iba neutrálne konštatovanie faktu a ponuka kontroly.
        """
        last_obs = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id
        ).order_by(WellbeingObservation.timestamp.desc()).first()

        if not last_obs or last_obs.alert_level < 2:
            return "" # Nie je dôvod na intervenciu

        if last_obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD:
            return "Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?"
            
        if last_obs.inferred_state == BehavioralState.AVOIDANCE:
            return "Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu."
            
        return "Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?"

    def get_class_balance_metrics(self, class_id: str, hours: int = 24) -> dict:
        """
        Vyhodnotí psychickú záťaž celej triedy/školy za posledných X hodín.
        Vracia percentuálny podiel aktivít v stave vysokého alertu.
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Počet udalostí s vysokým alertom (COGNITIVE_OVERLOAD, AVOIDANCE)
        high_alert_count = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.timestamp >= cutoff_time,
            WellbeingObservation.alert_level >= 2
        ).count()
        
        # Celkový počet udalostí za obdobie
        total_observations = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.timestamp >= cutoff_time
        ).count()
        
        # Výpočet pomeru (stress ratio)
        stress_ratio = (high_alert_count / total_observations * 100) if total_observations > 0 else 0.0
        
        return {
            "class_id": class_id,
            "timeframe_hours": hours,
            "high_alert_events": high_alert_count,
            "total_events": total_observations,
            "stress_ratio_percent": round(stress_ratio, 2),
            "requires_teacher_attention": stress_ratio > 15.0 # Threshold: 15%
        }
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

# Opravený import: začíname priamo od 'app'
from app.modules.k17_wellbeing_companion.repository.models import (
    WellbeingObservation, BehavioralState
)

class WellbeingAnalyticService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def record_observation(self, student_id: str, event_type: str, metrics: Dict[str, Any]) -> WellbeingObservation:
        """
        Zaznamená surové dáta a vypočíta aktuálny stav na základe kontextu.
        """
        # 1. Získaj posledných 5 pozorovaní tohto žiaka pre kontext (bazálna línia)
        recent_obs = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id
        ).order_by(WellbeingObservation.timestamp.desc()).limit(5).all()
        
        # 2. Analyzuj vzorec (Patrick Jane prístup: hľadaj nezrovnalosti v dátach)
        state, alert_level = self._analyze_pattern(metrics, recent_obs)

        # 3. Vytvor a ulož záznam
        observation = WellbeingObservation(
            id=str(uuid.uuid4()),
            student_id=student_id,
            event_type=event_type,
            metrics=metrics,
            inferred_state=state,
            alert_level=alert_level,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)
        return observation

    def _analyze_pattern(self, current_metrics: Dict[str, Any], history: List[WellbeingObservation]) -> tuple:
        """
        Detekcia stavu bez manipulácie. Iba matematika a behaviorálne vzorce.
        """
        consecutive_errors = current_metrics.get("consecutive_errors", 0)
        time_taken = current_metrics.get("time_taken_sec", 0)
        
        # Priemer času z histórie (ak existuje)
        avg_time = sum(o.metrics.get("time_taken_sec", 0) for o in history) / len(history) if history else 30.0
        
        # PRAVIDLO 1: Kognitívne preťaženie (Cognitive Overload)
        # Žiak robí chyby a čas sa predlžuje. Nie je to o inteligencii, je to o zablokovaní.
        if consecutive_errors >= 2 and time_taken > (avg_time * 1.5):
            return BehavioralState.COGNITIVE_OVERLOAD, 2
            
        # PRAVIDLO 2: Únik/Avoidance
        # Veľmi rýchla odpoveď (< 3 sekundy) po sérii chýb = náhodné klikanie a snaha mať to za sebou.
        if consecutive_errors >= 1 and time_taken < 3.0:
            return BehavioralState.AVOIDANCE, 2
            
        # PRAVIDLO 3: Flow (optimálny stav)
        # Čas je stabilný, chyby sú 0 alebo 1 (bežná korekcia).
        if consecutive_errors == 0 and (avg_time * 0.5) <= time_taken <= (avg_time * 1.2):
            return BehavioralState.FLOW, 0
            
        # Predvolený stav: Neutrálny (pokračuje v zabehnutom tempe)
        return BehavioralState.NEUTRAL, 0

    def get_intervention_prompt(self, student_id: str) -> str:
        """
        Vygeneruje text pre K-14 (Communication). 
        Pravidlo: Žiadna chvála ("Si šikovný!"), žiadny súcit ("To je ťažké, že?").
        Iba neutrálne konštatovanie faktu a ponuka kontroly.
        """
        last_obs = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id
        ).order_by(WellbeingObservation.timestamp.desc()).first()

        if not last_obs or last_obs.alert_level < 2:
            return "" # Nie je dôvod na intervenciu

        if last_obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD:
            return "Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?"
            
        if last_obs.inferred_state == BehavioralState.AVOIDANCE:
            return "Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu."
            
        return "Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?"

    def get_class_balance_metrics(self, class_id: str, hours: int = 24) -> dict:
        """
        Vyhodnotí psychickú záťaž celej triedy/školy za posledných X hodín.
        Vracia percentuálny podiel aktivít v stave vysokého alertu.
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Počet udalostí s vysokým alertom (COGNITIVE_OVERLOAD, AVOIDANCE)
        high_alert_count = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.timestamp >= cutoff_time,
            WellbeingObservation.alert_level >= 2
        ).count()
        
        # Celkový počet udalostí za obdobie
        total_observations = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.timestamp >= cutoff_time
        ).count()
        
        # Výpočet pomeru (stress ratio)
        stress_ratio = (high_alert_count / total_observations * 100) if total_observations > 0 else 0.0
        
        return {
            "class_id": class_id,
            "timeframe_hours": hours,
            "high_alert_events": high_alert_count,
            "total_events": total_observations,
            "stress_ratio_percent": round(stress_ratio, 2),
            "requires_teacher_attention": stress_ratio > 15.0 # Threshold: 15%
        }

    def get_latest_intervention_message(self, student_id: str) -> Optional[str]:
        """
        Vrátí neutrálnu správu pre študenta, ak bol v posledných 30 minútach 
        detekovaný stav s alert_level >= 2. Inak vráti None.
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        last_obs = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id,
            WellbeingObservation.timestamp >= cutoff,
            WellbeingObservation.alert_level >= 2
        ).order_by(WellbeingObservation.timestamp.desc()).first()

        if not last_obs:
            return None
            
        # Generovanie neutrálnej správy (Patrick Jane prístup: fakty + ponuka kontroly)
        if last_obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD:
            return "Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?"
        elif last_obs.inferred_state == BehavioralState.AVOIDANCE:
            return "Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu."
        
        return "Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?"


    def get_class_signals(self, student_ids, hours: int = 24) -> list:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = []
        for sid in student_ids:
            obs = self.db.query(WellbeingObservation).filter(
                WellbeingObservation.student_id == sid,
                WellbeingObservation.timestamp >= cutoff,
                WellbeingObservation.alert_level >= 2,
            ).order_by(WellbeingObservation.timestamp.desc()).first()
            if not obs:
                continue
            message = None
            if obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD:
                message = "Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?"
            elif obs.inferred_state == BehavioralState.AVOIDANCE:
                message = "Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu."
            else:
                message = "Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?"
            result.append({
                "student_id": str(sid),
                "inferred_state": obs.inferred_state.value if hasattr(obs.inferred_state, "value") else str(obs.inferred_state),
                "alert_level": obs.alert_level,
                "uncertainty": "high" if obs.alert_level >= 2 else "low",
                "triggered_by": obs.metrics,
                "message": message,
                "timestamp": obs.timestamp.isoformat() if hasattr(obs.timestamp, "isoformat") else str(obs.timestamp),
            })
        return result

    def get_child_messages(self, student_id, hours: int = 24) -> list:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        obs_list = self.db.query(WellbeingObservation).filter(
            WellbeingObservation.student_id == student_id,
            WellbeingObservation.timestamp >= cutoff,
            WellbeingObservation.alert_level >= 2,
        ).order_by(WellbeingObservation.timestamp.desc()).all()
        messages = []
        for obs in obs_list:
            if obs.inferred_state == BehavioralState.COGNITIVE_OVERLOAD:
                messages.append("Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?")
            elif obs.inferred_state == BehavioralState.AVOIDANCE:
                messages.append("Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu.")
            else:
                messages.append("Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?")
        # deduplikacia zachovanim poradia
        seen = set()
        unique = []
        for m in messages:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        return unique
