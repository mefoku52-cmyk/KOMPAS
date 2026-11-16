import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ensure backend on path and load .env
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)

from app.core.config.settings import settings  # noqa: E402
from app.core.database.session import Base  # noqa: E402
import app.core.audit.logger  # noqa: F401,E402
import app.core.events.bus  # noqa: F401,E402
import app.shared.identity  # noqa: F401,E402
import app.shared.school  # noqa: F401,E402
import app.shared.curriculum  # noqa: F401,E402
import app.modules.k16_intelligent_core.domain.models  # noqa: F401,E402
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

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
