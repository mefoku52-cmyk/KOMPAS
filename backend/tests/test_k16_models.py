def test_k16_tables_registered():
    import app.modules.k16_intelligent_core.domain.models  # noqa: F401
    from app.core.database.session import Base
    assert 'ai_knowledge_source' in Base.metadata.tables
    assert 'ai_knowledge_context_memory' in Base.metadata.tables
