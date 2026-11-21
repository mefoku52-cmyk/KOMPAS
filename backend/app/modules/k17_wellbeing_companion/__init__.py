from fastapi import FastAPI

from app.core.events.bus import EventBus
from app.modules.k17_wellbeing_companion.api.router import router
from app.modules.k17_wellbeing_companion.events.handlers import register as register_handlers


def register(app: FastAPI, bus: EventBus) -> None:
    register_handlers(bus)
    app.include_router(router)
