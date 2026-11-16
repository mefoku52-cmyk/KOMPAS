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
    from app.modules.k02_subject_workspace import register as register_k02
    from app.modules.k05_knowledge_continuity import register as register_k05
    from app.modules.k04_missions import register as register_k04
    from app.modules.k03_adaptive_learning import register as register_k03

    from app.modules.k09_class_overview import register as register_k09

    from app.modules.k07_professional_library import register as register_k07

    module_registrars = [register_k16, register_k01, register_k02, register_k05, register_k04, register_k03, register_k09, register_k07]
    for registrar in module_registrars:
        registrar(app, bus)

    return app


app = create_app()
