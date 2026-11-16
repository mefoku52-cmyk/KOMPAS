#!/usr/bin/env python3
"""Generate docs for phase 7: API contracts (OpenAPI), events catalog, permissions matrix copy, data model."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/.data/docgen.db")
os.environ.setdefault("JWT_SECRET_KEY", "docgen-secret-key-placeholder")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from app.main import app as fastapi_app  # noqa: E402
from fastapi.openapi.utils import get_openapi  # noqa: E402
from app.core.database.session import Base  # noqa: E402
import app.core.audit.logger  # noqa: F401,E402
import app.core.events.bus  # noqa: F401,E402
import app.shared.identity  # noqa: F401,E402
import app.shared.school  # noqa: F401,E402
import app.shared.curriculum  # noqa: F401,E402
for m in [
    "k01_learning_profile","k02_subject_workspace","k03_adaptive_learning","k04_missions",
    "k05_knowledge_continuity","k06_virtual_lab","k07_professional_library","k08_work_assistant",
    "k09_class_overview","k10_organization_center","k11_operations_center","k12_analytics_center",
    "k13_parent_center","k14_communication_center","k15_collaboration_projects","k16_intelligent_core",
]:
    __import__(f"app.modules.{m}.domain.models")

# API contracts
schema = get_openapi(title="KOMPAS API", version="0.1.0", routes=fastapi_app.routes)
(ROOT/"docs/api-contracts/openapi.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
lines = ["# API kontrakty", "", "Generované z OpenAPI (`app.openapi()`). Zdroj: `docs/api-contracts/openapi.json`.", "", "## Endpointy", ""]
for path, methods in sorted(schema.get("paths", {}).items()):
    for method, info in sorted(methods.items()):
        if method.lower() not in {"get","post","put","patch","delete"}:
            continue
        summary = info.get("summary") or info.get("operationId") or ""
        tags = ",".join(info.get("tags", []))
        auth = "áno" if info.get("security") else "nie (verejné alebo nešpecifikované v schéme)"
        lines.append(f"- `{method.upper()} {path}` - {summary} (tagy: {tags or '-'}, security v schéme: {auth})")
(ROOT/"docs/api-contracts/README.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

# Events
events = ["# Katalóg udalostí", "", "## Infraštruktúra", "- Zbernica: `app.core.events.bus.EventBus` (typ `DomainEvent`: event_id, event_type, čas, school_id, payload).", "- Perzistencia: `audit_event_log`, izolácia chýb handlera (log, publikujúci nespadne).", "", "## Publikované/odoberané udalosti (aktuálny stav)", "- `AnswerEvaluated` / `learning.answer_evaluated` - publikuje K-04 (vyhodnotenie pokusu), odoberá K-05 (zápis stavu témy: precvičené/čiastočne zvládnuté; overené zvládnutie len pri verifikačnom pokuse).", "- Ostatné moduly v aktuálnom rozsahu bez doménových publikácií/odberov (registrujú handlery/routery).", ""]
(ROOT/"docs/events/README.md").write_text("\n".join(events), encoding="utf-8")

# Data model
area_prefixes = {"identity":"identity_","school":"school_","curriculum":"curriculum_","learning":"learning_","progress":"progress_","teacher_workspace":"teacher_workspace_","organization":"organization_","communication":"communication_","ai_knowledge":"ai_knowledge_","audit":"audit_"}
table_to_area={"audit_event_log":"audit"}
def area_of(name):
    if name in table_to_area: return table_to_area[name]
    for a,p in area_prefixes.items():
        if name.startswith(p): return a
    return "other"
by_area={a:[] for a in area_prefixes}
for t in Base.metadata.sorted_tables:
    by_area.setdefault(area_of(t.name), []).append(t)
dm=["# Dátový model", "", "Generované z SQLAlchemy metadata (zdroj pravdy schémy). Tabuľky sú podľa prefixov oblastí (D3).", ""]
for a in list(area_prefixes.keys())+([k for k in by_area if k not in area_prefixes] or []):
    tabs=by_area.get(a,[])
    dm.append(f"## Oblasť: {a}")
    if not tabs:
        dm.append("- (bez tabuliek)")
    for t in sorted(tabs,key=lambda x:x.name):
        cols=", ".join(f"{c.name}:{c.type}" for c in t.columns)
        dm.append(f"- `{t.name}` ({cols})")
    dm.append("")
(ROOT/"docs/data-model/README.md").write_text("\n".join(dm), encoding="utf-8")

print("generated api-contracts/events/data-model")
