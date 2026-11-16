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


@pytest.fixture()
def db_session(tmp_path):
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
