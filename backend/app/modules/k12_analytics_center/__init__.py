from app.modules.k12_analytics_center.api.router import router


def register(app, event_bus):
    app.include_router(router)
