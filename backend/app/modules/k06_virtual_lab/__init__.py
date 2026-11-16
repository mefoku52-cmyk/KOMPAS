from app.modules.k06_virtual_lab.api.router import router


def register(app, event_bus):
    from app.modules.k06_virtual_lab.events.handlers import register as register_events

    app.include_router(router)
    register_events(event_bus)
