import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

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
    "sis": "sis_",
    "wellbeing": "k17_",
    "intelligence": "il_",
}
TABLE_TO_AREA = {"audit_event_log": "audit"}


def _load_metadata():
    os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/schema.db")
    os.environ.setdefault("JWT_SECRET_KEY", "schema-test-placeholder")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    import app.core.audit.logger  # noqa: F401
    import app.core.events.bus  # noqa: F401
    import app.shared.curriculum  # noqa: F401
    import app.shared.identity  # noqa: F401
    import app.shared.school  # noqa: F401
    from app.core.database.session import Base

    return Base.metadata


def table_area(name: str) -> str:
    if name in TABLE_TO_AREA:
        return TABLE_TO_AREA[name]
    matches = [area for area, prefix in AREA_PREFIXES.items() if name.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"table {name} must match exactly one area, got {matches}")
    return matches[0]


def test_table_naming_convention_d3_and_schema_files():
    metadata = _load_metadata()
    tables = list(metadata.tables.keys())
    assert tables, "no tables found"
    areas_seen = set()
    for t in tables:
        areas_seen.add(table_area(t))
    assert areas_seen
    schema_dir = ROOT / "db" / "schema"
    for area in AREA_PREFIXES:
        p = schema_dir / f"{area}.sql"
        assert p.exists(), f"missing schema file for {area}"
        content = p.read_text(encoding="utf-8")
        assert content.strip(), f"schema file must be non-empty: {p}"
        if "No tables defined yet" in content:
            assert f"area: {area}" in content
        else:
            assert "CREATE TABLE" in content
    assert set(AREA_PREFIXES.keys()) == {p.stem for p in schema_dir.glob("*.sql")}


def test_no_cross_module_internal_imports():
    modules_dir = ROOT / "backend" / "app" / "modules"
    modules = [p.name for p in modules_dir.iterdir() if p.is_dir() and p.name.startswith("k")]
    forbidden = ("domain", "repository", "services")
    violations = []
    for mod in modules:
        mod_path = modules_dir / mod
        for py in mod_path.rglob("*.py"):
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    m = node.module
                    if m.startswith("app.modules."):
                        parts = m.split(".")
                        # app.modules.<other>.<layer>
                        if len(parts) >= 4:
                            other = parts[2]
                            layer = parts[3]
                            if other != mod and other in modules and layer in forbidden:
                                violations.append(f"{py}: imports {m}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        m = alias.name
                        if m.startswith("app.modules."):
                            parts = m.split(".")
                            if len(parts) >= 4:
                                other = parts[2]
                                layer = parts[3]
                                if other != mod and other in modules and layer in forbidden:
                                    violations.append(f"{py}: imports {m}")
    assert not violations, "cross-module internal imports: " + "; ".join(violations)
