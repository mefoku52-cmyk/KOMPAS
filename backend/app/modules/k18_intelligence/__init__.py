from fastapi import FastAPI

from app.core.events.bus import EventBus
from app.modules.k18_intelligence.api.router import router
from app.modules.k18_intelligence.api.role_router import router as role_router
from app.modules.k18_intelligence.api.ops_router import router as ops_router
from app.modules.k18_intelligence.events.handlers import register as register_handlers


def register(app: FastAPI, bus: EventBus) -> None:
    register_handlers(bus)
    app.include_router(router)
    app.include_router(role_router)
    app.include_router(ops_router)
