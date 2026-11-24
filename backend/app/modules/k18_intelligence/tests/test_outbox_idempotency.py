import uuid

from sqlalchemy import select

from app.modules.k18_intelligence.repository.outbox import ILOutbox, ILInbox, enqueue_outbox, process_once


def test_enqueue_outbox_is_idempotent(db_session):
    event_id = uuid.uuid4()
    first = enqueue_outbox(db_session, event_id, "mission.completed", {"school_id": "school-a"})
    second = enqueue_outbox(db_session, event_id, "mission.completed", {"school_id": "school-a"})
    db_session.commit()
    assert first.id == second.id
    assert db_session.execute(select(ILOutbox).where(ILOutbox.event_id == event_id)).scalars().all() == [first]


def test_outbox_retry_updates_failed_inbox_row(db_session):
    event_id = uuid.uuid4()
    item = enqueue_outbox(db_session, event_id, "mission.completed", {"school_id": "school-a"})
    db_session.commit()
    class Orchestrator:
        def process_event(self, *args, **kwargs):
            return {"status": "processed"}
    calls = {"n": 0}
    def factory(db):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("temporary failure")
        return Orchestrator()
    assert process_once(db_session, factory)["failed"] == 1
    db_session.commit()
    assert process_once(db_session, factory)["processed"] == 1
    db_session.commit()
    inbox = db_session.execute(select(ILInbox).where(ILInbox.event_id == event_id)).scalar_one()
    assert inbox.status == "done" and inbox.attempts == 2 and inbox.last_error is None
    assert item.status == "done"
