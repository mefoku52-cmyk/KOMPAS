from fastapi import FastAPI

from app.core.events.bus import EventBus
from app.modules.k19_sis_integration.api.router import router


def register(app: FastAPI, bus: EventBus) -> None:
    app.include_router(router)
