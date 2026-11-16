from __future__ import annotations

from app.core.events.bus import DomainEvent, EventBus


def register(bus: EventBus) -> None:
    # K-16 subscribes to relevant events later (analytics/audit read side). No-op for now.
    _ = bus
    return None
