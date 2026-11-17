import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ensure env loaded
ROOT = Path(__file__).resolve().parents[1]
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/.data/test_phase1.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789abcdef")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from app.core.database.session import Base  # noqa: E402
import app.core.audit.logger  # noqa: F401,E402
import app.core.events.bus  # noqa: F401,E402
import app.shared.identity  # noqa: F401,E402
import app.shared.school  # noqa: F401,E402
import app.shared.curriculum  # noqa: F401,E402
import app.modules.k01_learning_profile.domain.models  # noqa: F401,E402
import app.modules.k02_subject_workspace.domain.models  # noqa: F401,E402
import app.modules.k05_knowledge_continuity.domain.models  # noqa: F401,E402
import app.modules.k04_missions.domain.models  # noqa: F401,E402
import app.modules.k03_adaptive_learning.domain.models  # noqa: F401,E402
import app.modules.k09_class_overview.domain.models  # noqa: F401,E402
import app.modules.k07_professional_library.domain.models  # noqa: F401,E402
import app.modules.k08_work_assistant.domain.models  # noqa: F401,E402
import app.modules.k10_organization_center.domain.models  # noqa: F401,E402
import app.modules.k11_operations_center.domain.models  # noqa: F401,E402
import app.modules.k12_analytics_center.domain.models  # noqa: F401,E402
import app.modules.k14_communication_center.domain.models  # noqa: F401,E402
import app.modules.k15_collaboration_projects.domain.models  # noqa: F401,E402
import app.modules.k06_virtual_lab.domain.models  # noqa: F401,E402
import app.modules.k09_class_overview.domain.models  # noqa: F401,E402
import app.modules.k13_parent_center.domain.models  # noqa: F401,E402
import app.modules.k16_intelligent_core.domain.models  # noqa: F401,E402


PG_TEST_URL = os.environ.get("KOMPAS_TEST_DATABASE_URL", "")
if not PG_TEST_URL and os.environ.get("DATABASE_URL", "").startswith("postgres"):
    PG_TEST_URL = os.environ["DATABASE_URL"]


def _defer_pg_foreign_keys(engine) -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT c.conname, c.conrelid::regclass::text AS table_name "
            "FROM pg_constraint c "
            "JOIN pg_namespace n ON n.oid = c.connamespace "
            "WHERE c.contype = 'f' AND n.nspname = current_schema()"
        )).all()
        for name, table_name in rows:
            conn.execute(text(
                f'ALTER TABLE {table_name} ALTER CONSTRAINT "{name}" DEFERRABLE INITIALLY DEFERRED'
            ))


@pytest.fixture()
def db_session(tmp_path):
    if PG_TEST_URL:
        from sqlalchemy.pool import NullPool
        engine = create_engine(PG_TEST_URL, poolclass=NullPool, future=True)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        _defer_pg_foreign_keys(engine)
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(engine)
            engine.dispose()
        return
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
