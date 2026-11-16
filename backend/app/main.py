from fastapi import FastAPI

from app.core.config.settings import settings
from app.core.events.bus import bus
from app.core.security.routes import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth_router)

    # Module registration mechanism: each module exposes register(app, bus)
    from app.modules.k16_intelligent_core import register as register_k16
    from app.modules.k01_learning_profile import register as register_k01

    module_registrars = [register_k16, register_k01]
    for registrar in module_registrars:
        registrar(app, bus)

    return app


app = create_app()
