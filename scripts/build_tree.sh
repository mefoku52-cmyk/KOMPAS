#!/usr/bin/env bash
set -eu
ROOT="$HOME/KOMPAS"

# Vytvorí prázdny súbor (a jeho adresár), existujúci súbor nechá nedotknutý
mk() {
  mkdir -p "$(dirname "$ROOT/$1")"
  [ -e "$ROOT/$1" ] || : > "$ROOT/$1"
}

MODS="k01_learning_profile k02_subject_workspace k03_adaptive_learning k04_missions k05_knowledge_continuity k06_virtual_lab k07_professional_library k08_work_assistant k09_class_overview k10_organization_center k11_operations_center k12_analytics_center k13_parent_center k14_communication_center k15_collaboration_projects k16_intelligent_core"

# --- koren ---
mk README.md
mk .gitignore
mk .env.example

# --- backend: aplikacia a jadro ---
mk backend/requirements.txt
mk backend/pyproject.toml
mk backend/app/__init__.py
mk backend/app/main.py
for c in config security database events audit permissions; do
  mk "backend/app/core/$c/__init__.py"
done
mk backend/app/core/__init__.py
mk backend/app/core/config/settings.py
mk backend/app/core/security/auth.py
mk backend/app/core/database/session.py
mk backend/app/core/events/bus.py
mk backend/app/core/audit/logger.py
mk backend/app/core/permissions/policy.py
mk backend/app/shared/__init__.py
mk backend/app/shared/types.py

# --- backend: 16 modulov ---
mk backend/app/modules/__init__.py
for m in $MODS; do
  b="backend/app/modules/$m"
  mk "$b/__init__.py"
  for s in api domain services repository events tests; do
    mk "$b/$s/__init__.py"
  done
  mk "$b/api/router.py"
  mk "$b/domain/models.py"
  mk "$b/services/service.py"
  mk "$b/repository/repository.py"
  mk "$b/events/handlers.py"
  mk "$b/tests/test_service.py"
done

# --- K-16: podsystemy inteligentneho jadra ---
for p in orchestrator knowledge_system context_memory rule_system analytics_engine audit_engine; do
  mk "backend/app/modules/k16_intelligent_core/$p/__init__.py"
  mk "backend/app/modules/k16_intelligent_core/$p/service.py"
done

# --- databaza: 10 datovych oblasti z dokumentu ---
for d in identity school curriculum learning progress teacher_workspace organization communication ai_knowledge audit; do
  mk "db/schema/$d.sql"
done
mk db/migrations/.gitkeep
mk db/seeds/.gitkeep

# --- frontend ---
mk frontend/package.json
mk frontend/tsconfig.json
mk frontend/src/app/layout.tsx
mk frontend/src/app/page.tsx
for r in student teacher leadership parent; do
  mk "frontend/src/app/$r/page.tsx"
done
mk frontend/src/components/.gitkeep
mk frontend/src/lib/api.ts
mk frontend/src/locales/.gitkeep
mk frontend/tests/.gitkeep

# --- lokalizacie ---
for l in sk en; do
  mk "locales/$l/common.json"
done

# --- dokumentacia ---
mk docs/architecture/system_architecture.md
mk docs/adr/0001-identity-partner.md
mk docs/api-contracts/README.md
mk docs/events/README.md
mk docs/permissions/README.md
mk docs/data-model/README.md
mk docs/research/README.md
mk docs/metrics/README.md
for i in $(seq 1 16); do
  mk "docs/modules/K-$(printf '%02d' "$i").md"
done

# --- testy a infrastruktura ---
mk tests/integration/test_smoke.py
mk tests/e2e/.gitkeep
mk infra/docker/.gitkeep
mk infra/ops/.gitkeep

echo "BUILD DOKONCENY"
