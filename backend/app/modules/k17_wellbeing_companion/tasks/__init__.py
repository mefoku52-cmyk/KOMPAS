EOF
cat > backend/app/modules/k17_wellbeing_companion/tasks/processor.py <<'PY'
import asyncio
import logging

from app.core.config.settings import settings
from app.core.database.session import SessionLocal

logger = logging.getLogger("kompas.k17.tasks")


def process_once(db) -> int:
    """
    Idempotentné spracovanie počas nečinnosti.
    Vráti počet spracovaných udalostí (0 ak nič nové).
    """
    # Žiadny backlog v tejto etape; handler spracováva udalosti synchronne.
    # Funkcia je tu pre plánovanú úlohu a test dvojitého spustenia.
    return 0


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
