from app.modules.k14_communication_center.api.router import router


def register(app, event_bus):
    from app.modules.k14_communication_center.events.handlers import register as register_events

    app.include_router(router)
    register_events(event_bus)
