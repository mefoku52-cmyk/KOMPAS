import uuid

import pytest

from app.modules.k16_intelligent_core.context_memory.service import ContextMemoryService
from app.modules.k16_intelligent_core.knowledge_system.service import KnowledgeSystemService
from app.modules.k16_intelligent_core.orchestrator.service import NullProvider, OrchestratorService
from app.modules.k16_intelligent_core.rule_system.service import FORBIDDEN_AI_ACTIONS, RuleSystemService
from app.shared.types import Principal, Role, system_principal


def sys_p(school_id):
    p = system_principal()
    # attach school for authorize context checks where needed
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def test_rule_system_denies_forbidden_and_allows_allowed_fields(db_session):
    rs = RuleSystemService()
    school_id = uuid.uuid4()
    p = Principal(user_id=uuid.uuid4(), role=Role.TEACHER, school_id=school_id)
    sp = sys_p(school_id)
    # forbidden
    for action in FORBIDDEN_AI_ACTIONS:
        d = rs.evaluate(p, action, requested_fields=["topic_id"], context={"system_internal": False})
        assert d.allowed is False and d.reason == "forbidden_ai_action"
    # disallowed field with system principal to pass permission gate
    d2 = rs.evaluate(sp, "ai.help", requested_fields=["secret_personality"], context={"system_internal": True})
    assert d2.allowed is False and d2.reason == "disallowed_fields"
    d3 = rs.evaluate(sp, "ai.help", requested_fields=["topic_id"], context={"system_internal": True})
    assert d3.allowed is True


def test_knowledge_search_only_approved(db_session):
    school_id = uuid.uuid4()
    sp = sys_p(school_id)
    ks = KnowledgeSystemService(db_session)
    ks.register_source(sp, school_id, "Std", "standard", "math basics algebra", approved=True)
    ks.register_source(sp, school_id, "Draft", "material", "math draft", approved=False)
    db_session.commit()
    res = ks.search_approved(sp, school_id, "math")
    assert len(res) == 1 and res[0].name == "Std"
    res2 = ks.search_approved(sp, school_id, "draft")
    assert len(res2) == 0


def test_context_memory_requires_source_ref(db_session):
    school_id = uuid.uuid4()
    sp = sys_p(school_id)
    cm = ContextMemoryService(db_session)
    with pytest.raises(ValueError):
        cm.add_record(sp, school_id, "", "x")
    obj = cm.add_record(sp, school_id, "progress:abc", "note")
    assert obj.source_record_ref == "progress:abc"


def test_orchestrator_nullprovider_and_audit(db_session):
    school_id = uuid.uuid4()
    sp = sys_p(school_id)
    orch = OrchestratorService(db_session, providers={"null": NullProvider()}, rule_system=RuleSystemService())
    out = orch.run(sp, "help", "prompt", payload={"topic_id": "t1"}, context={"system_internal": True})
    assert out == "[null:help]"
    # forbidden action denied and audited
    with pytest.raises(PermissionError):
        orch.run(sp, "pedagogical_decision", "p", payload={}, context={"system_internal": True})
    # check audit entries exist
    from sqlalchemy import select
    from app.core.audit.logger import AuditLog
    rows = db_session.execute(select(AuditLog).where(AuditLog.action.in_(["ai.orchestrator.call"])) ).scalars().all()
    assert len(rows) >= 2
    outcomes = {r.outcome for r in rows}
    assert "success" in outcomes and "denied" in outcomes
