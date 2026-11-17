from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import settings
from app.core.errors import install_error_handlers
from app.core.events.bus import bus
from app.core.security.routes import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None, openapi_url=None)
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

    module_registrars = [register_k16, register_k01, register_k02, register_k05, register_k04, register_k03, register_k09, register_k07, register_k08, register_k10, register_k11, register_k12, register_k13, register_k14, register_k15, register_k06]
    for registrar in module_registrars:
        registrar(app, bus)

    return app


app = create_app()
