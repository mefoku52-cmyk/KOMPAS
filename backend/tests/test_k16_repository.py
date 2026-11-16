import uuid

from app.modules.k16_intelligent_core.repository.repository import K16Repository


def test_repository_source_and_memory(db_session):
    school_id = uuid.uuid4()
    repo = K16Repository(db_session)
    s1 = repo.create_source(school_id=school_id, name="Std", source_type="standard", content="math basics", approved=True)
    repo.create_source(school_id=school_id, name="Draft", source_type="material", content="draft", approved=False)
    approved = repo.list_approved_sources(school_id)
    assert [x.id for x in approved] == [s1.id]

    mem = repo.create_context_memory(school_id=school_id, source_record_ref="progress:1", content="note")
    assert mem.source_record_ref == "progress:1"
    assert len(repo.list_context_memories(school_id)) == 1

    try:
        repo.create_context_memory(school_id=school_id, source_record_ref="", content="bad")
        assert False, "expected ValueError"
    except ValueError:
        pass
