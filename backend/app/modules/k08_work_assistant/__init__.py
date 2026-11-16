from fastapi import FastAPI

from app.core.events.bus import EventBus
from app.modules.k08_work_assistant.api.router import router
from app.modules.k08_work_assistant.events.handlers import register as register_handlers


def register(app: FastAPI, bus: EventBus) -> None:
    register_handlers(bus)
    app.include_router(router)
