from app.modules.k15_collaboration_projects.api.router import router


def register(app, event_bus):
    from app.modules.k15_collaboration_projects.events.handlers import register as register_events

    app.include_router(router)
    register_events(event_bus)
