from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config.settings import Settings, settings
from app.modules.k08_work_assistant.services.service import K08Service
from app.modules.k16_intelligent_core.orchestrator.service import NullProvider, OrchestratorService
from app.shared.identity import User
from app.shared.school import School
from app.shared.types import Principal, Role


def test_ai_configuration_has_only_null_provider():
    assert settings.ai_provider == "null"
    assert settings.ai_external_enabled is False
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, DATABASE_URL="sqlite:///x.db", JWT_SECRET_KEY="test-secret-key-0123456789abcdef",
            AI_PROVIDER="openai",
        )
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, DATABASE_URL="sqlite:///x.db", JWT_SECRET_KEY="test-secret-key-0123456789abcdef",
            AI_EXTERNAL_ENABLED="true",
        )


def test_k08_template_mode_without_external_provider(db_session):
    school_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    db_session.add(School(id=school_id, name=f"AI-{school_id}", is_demo=True))
    db_session.add(User(id=teacher_id, school_id=school_id, username=f"t-{teacher_id}", full_name="T", password_hash="x", is_demo=True))
    db_session.commit()
    teacher = Principal(user_id=teacher_id, role=Role.TEACHER, school_id=school_id)
    draft = K08Service(db_session).generate_draft(
        teacher, school_id=school_id, teacher_user_id=teacher_id,
        title="Zlomky", draft_type="worksheet", topics=["Zlomky"], use_orchestrator=True,
    )
    assert "sablonovy navrh" in draft.content
    assert draft.content.startswith("Navrh: worksheet")


def test_k16_orchestrator_uses_deterministic_null_provider(db_session):
    orchestrator = OrchestratorService(db_session)
    assert isinstance(orchestrator.select_provider("unknown-task"), NullProvider)
    principal = Principal(user_id=uuid.uuid4(), role=None, scopes=("system",), is_system=True)
    first = orchestrator.run(principal, "help", "prompt", payload={"topic_id": "t1"}, context={"system_internal": True})
    second = orchestrator.run(principal, "help", "prompt", payload={"topic_id": "t1"}, context={"system_internal": True})
    assert first == second == "[null:help]"
