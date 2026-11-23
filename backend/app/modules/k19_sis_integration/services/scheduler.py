from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.modules.k19_sis_integration.domain.models import SISJobMode, SISSource
from app.modules.k19_sis_integration.services.sync_service import SISService
from app.shared.types import system_principal

logger = logging.getLogger("kompas.sis")


def run_enabled_sources_once() -> list[dict]:
    db = SessionLocal()
    results: list[dict] = []
    try:
        sources = list(db.execute(select(SISSource).where(SISSource.is_enabled.is_(True))).scalars().all())
        for src in sources:
            try:
                principal = system_principal(school_id=src.school_id)
                job = SISService(db).run_sync(principal, school_id=src.school_id, source_id=src.id, mode=SISJobMode.FULL.value)
                db.commit()
                results.append({"source_id": str(src.id), "status": job.get("status")})
            except Exception as exc:
                db.rollback()
                logger.exception("SIS auto-sync failed for source %s", src.id)
                results.append({"source_id": str(src.id), "status": "failed", "error": str(exc)})
    finally:
        db.close()
    return results


async def processing_loop(stop_event: asyncio.Event) -> None:
    if not settings.sis_sync_enabled or not settings.sis_auto_sync_enabled:
        return
    interval = max(300, int(settings.sis_sync_interval_minutes) * 60)
    while not stop_event.is_set():
        try:
            run_enabled_sources_once()
        except Exception:
            logger.exception("SIS auto-sync loop failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
