from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import settings
from app.core.errors import install_error_handlers
from app.core.events.bus import bus
from app.core.privacy import router as privacy_router
from app.core.security.routes import router as auth_router

# Model registration: not every module imports its ORM models on startup. Without
# these imports Base.metadata misses tables that permission checks and serializers
# rely on (k09 teacher-of-class lookup, curriculum topic names in k04 missions).
import app.shared.curriculum  # noqa: F401,E402
import app.modules.k09_class_overview.domain.models  # noqa: F401,E402


def _docs_enabled() -> bool:
    # Swagger is a development aid; production stays closed unless explicitly enabled.
    return settings.app_docs_enabled or settings.app_env != "production"


def create_app() -> FastAPI:
    docs = "/docs" if _docs_enabled() else None
    openapi = "/openapi.json" if _docs_enabled() else None
    app = FastAPI(title=settings.app_name, docs_url=docs, redoc_url=None, openapi_url=openapi)
    install_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(privacy_router)

    # Module registration mechanism: each module exposes register(app, bus)
    from app.modules.k16_intelligent_core import register as register_k16
    from app.modules.k01_learning_profile import register as register_k01
    from app.modules.k02_subject_workspace import register as register_k02
    from app.modules.k05_knowledge_continuity import register as register_k05
    from app.modules.k04_missions import register as register_k04
    from app.modules.k03_adaptive_learning import register as register_k03

    from app.modules.k09_class_overview import register as register_k09

    from app.modules.k07_professional_library import register as register_k07

    from app.modules.k08_work_assistant import register as register_k08

    from app.modules.k10_organization_center import register as register_k10
    from app.modules.k11_operations_center import register as register_k11

    from app.modules.k12_analytics_center import register as register_k12
    from app.modules.k13_parent_center import register as register_k13
    from app.modules.k14_communication_center import register as register_k14
    from app.modules.k15_collaboration_projects import register as register_k15
    from app.modules.k06_virtual_lab import register as register_k06
    from app.modules.k17_wellbeing_companion import register as register_k17
    from app.modules.k18_intelligence import register as register_k18

    module_registrars = [register_k16, register_k01, register_k02, register_k05, register_k04, register_k03, register_k09, register_k07, register_k08, register_k10, register_k11, register_k12, register_k13, register_k14, register_k15, register_k06, register_k17, register_k18]
    for registrar in module_registrars:
        registrar(app, bus)

    @app.on_event("startup")
    async def _k17_startup() -> None:
        import asyncio
        from app.modules.k17_wellbeing_companion.tasks.processor import processing_loop

        app.state.k17_stop_event = asyncio.Event()
        app.state.k17_task = asyncio.create_task(processing_loop(app.state.k17_stop_event))

    @app.on_event("shutdown")
    async def _k17_shutdown() -> None:
        stop_event = getattr(app.state, "k17_stop_event", None)
        task = getattr(app.state, "k17_task", None)
        if stop_event is not None:
            stop_event.set()
        if task is not None:
            await task

    return app


app = create_app()
