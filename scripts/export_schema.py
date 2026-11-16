#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from sqlalchemy import create_mock_engine
from sqlalchemy.schema import CreateIndex

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/schema.db")
os.environ.setdefault("JWT_SECRET_KEY", "schema-export-placeholder")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

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

AREA_PREFIXES = {
    "identity": "identity_",
    "school": "school_",
    "curriculum": "curriculum_",
    "learning": "learning_",
    "progress": "progress_",
    "teacher_workspace": "teacher_workspace_",
    "organization": "organization_",
    "communication": "communication_",
    "ai_knowledge": "ai_knowledge_",
    "audit": "audit_",
}

TABLE_TO_AREA = {
    "audit_event_log": "audit",
}


def table_area(name: str) -> str:
    if name in TABLE_TO_AREA:
        return TABLE_TO_AREA[name]
    for area, prefix in AREA_PREFIXES.items():
        if name.startswith(prefix):
            return area
    raise ValueError(f"Unknown area for table: {name}")


def main() -> int:
    out_dir = ROOT / "db" / "schema"
    out_dir.mkdir(parents=True, exist_ok=True)
    statements: dict[str, list[str]] = {k: [] for k in AREA_PREFIXES}
    seen_sql: dict[str, set[str]] = {k: set() for k in AREA_PREFIXES}

    def dump(sql, *multiparams, **params):
        compiled = sql.compile(dialect=engine.dialect)
        text_sql = str(compiled).strip()
        if not text_sql:
            return
        if not text_sql.endswith(";"):
            text_sql += ";"
        if text_sql in seen_sql[current_area]:
            return
        seen_sql[current_area].add(text_sql)
        statements[current_area].append(text_sql)

    engine = create_mock_engine("postgresql://", dump)
    tables = sorted(Base.metadata.tables.values(), key=lambda t: t.name)
    global current_area
    current_area = "audit"
    for table in tables:
        current_area = table_area(table.name)
        table.create(engine, checkfirst=False)
        for idx in sorted(table.indexes, key=lambda i: i.name or ""):
            if idx.name:
                engine.execute(CreateIndex(idx))

    for area, stmts in statements.items():
        path = out_dir / f"{area}.sql"
        if stmts:
            content = "\n\n".join(stmts) + "\n"
        else:
            content = f"-- Generated PostgreSQL DDL for area: {area}\n-- No tables defined yet.\n"
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path} ({len(stmts)} statements)")

    for area in AREA_PREFIXES:
        if not (out_dir / f"{area}.sql").exists():
            raise SystemExit(f"missing schema file for area {area}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
