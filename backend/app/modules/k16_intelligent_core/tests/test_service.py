import uuid

import pytest

from app.modules.k16_intelligent_core.context_memory.service import ContextMemoryService
from app.modules.k16_intelligent_core.knowledge_system.service import KnowledgeSystemService
from app.modules.k16_intelligent_core.orchestrator.service import NullProvider, OrchestratorService
from app.modules.k16_intelligent_core.rule_system.service import FORBIDDEN_AI_ACTIONS, RuleSystemService
from app.shared.types import Principal, Role, system_principal


def _sys_principal(school_id):
    p = system_principal()
    return Principal(user_id=p.user_id, role=None, school_id=school_id, scopes=p.scopes, is_system=True)


def test_k16_rule_system_positive_and_negative_permissions(db_session):
    rs = RuleSystemService()
    school_id = uuid.uuid4()
    sp = _sys_principal(school_id)
    teacher = Principal(user_id=uuid.uuid4(), role=Role.TEACHER, school_id=school_id)

    # negative: forbidden AI actions
    for action in FORBIDDEN_AI_ACTIONS:
        d = rs.evaluate(teacher, action, requested_fields=["topic_id"], context={"system_internal": False})
        assert d.allowed is False
        assert d.reason == "forbidden_ai_action"

    # negative: disallowed fields
    d_bad_fields = rs.evaluate(sp, "ai.help", requested_fields=["secret_personality"], context={"system_internal": True})
    assert d_bad_fields.allowed is False
    assert d_bad_fields.reason == "disallowed_fields"

    # positive: allowed fields with permitted context
    d_ok = rs.evaluate(sp, "ai.help", requested_fields=["topic_id", "score"], context={"system_internal": True})
    assert d_ok.allowed is True


def test_k16_knowledge_search_only_approved_and_permission_denied(db_session):
    school_id = uuid.uuid4()
    sp = _sys_principal(school_id)
    ks = KnowledgeSystemService(db_session)
    ks.register_source(sp, school_id, "Std", "standard", "math basics algebra", approved=True)
    ks.register_source(sp, school_id, "Draft", "material", "math draft", approved=False)
    db_session.commit()

    # positive
    res = ks.search_approved(sp, school_id, "math")
    assert len(res) == 1 and res[0].name == "Std"

    # negative permission: principal without system_internal and no granted scope denied by default
    outsider = Principal(user_id=uuid.uuid4(), role=Role.TEACHER, school_id=school_id)
    with pytest.raises(PermissionError):
        ks.search_approved(outsider, school_id, "math")


def test_k16_context_memory_requires_source_and_permission(db_session):
    school_id = uuid.uuid4()
    sp = _sys_principal(school_id)
    cm = ContextMemoryService(db_session)

    # negative: missing source ref
    with pytest.raises(ValueError):
        cm.add_record(sp, school_id, "", "x")

    # positive
    obj = cm.add_record(sp, school_id, "progress:abc", "note")
    assert obj.source_record_ref == "progress:abc"

    # negative permission
    outsider = Principal(user_id=uuid.uuid4(), role=Role.TEACHER, school_id=school_id)
    with pytest.raises(PermissionError):
        cm.add_record(outsider, school_id, "progress:def", "note")


def test_k16_orchestrator_audits_and_denies_forbidden(db_session):
    school_id = uuid.uuid4()
    sp = _sys_principal(school_id)
    orch = OrchestratorService(db_session, providers={"null": NullProvider()}, rule_system=RuleSystemService())

    # positive
    out = orch.run(sp, "help", "prompt", payload={"topic_id": "t1"}, context={"system_internal": True})
    assert out == "[null:help]"

    # negative: forbidden action
    with pytest.raises(PermissionError):
        orch.run(sp, "pedagogical_decision", "p", payload={}, context={"system_internal": True})
