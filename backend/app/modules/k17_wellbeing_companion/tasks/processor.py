import asyncio
import logging

from app.core.config.settings import settings
from app.core.database.session import SessionLocal

logger = logging.getLogger("kompas.k17.tasks")


def process_once(db) -> int:
    """
    Idempotentne spracovanie pocas necinnosti.
    Vrati pocet spracovanych udalosti (0 ak nic nove).
    """
    return 0


def purge_old_observations(db) -> int:
    """
    Vymaze pozorovania starsie nez K17_RETENTION_DAYS.
    Idempotentne: opakovane spustenie nema dalsi efekt.
    """
    from datetime import datetime, timedelta, timezone
    from app.modules.k17_wellbeing_companion.repository.models import WellbeingObservation

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.k17_retention_days)
    q = db.query(WellbeingObservation).filter(WellbeingObservation.timestamp < cutoff)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


async def processing_loop(stop_event: asyncio.Event) -> None:
    interval = settings.k17_processing_interval_seconds
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                process_once(db)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error("K17 processing loop error: %s", e, exc_info=True)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
