#!/usr/bin/env bash
# Použitie: bash ~/KOMPAS/scripts/check_phase.sh <0-7>   alebo   ... msgs
ROOT="$HOME/KOMPAS"
PY="$ROOT/backend/.venv/bin/python"

next_msg() {
  case "$1" in
    0) printf '%s\n' "FÁZA 0 schválená (nezávislá kontrola scripts/check_phase.sh 0 prešla). Pokračuj FÁZOU 1 podľa docs/OPENCODE_PROMPT.md. Povolená výnimka z pravidla 6: vytvor aj scripts/make_env.sh, ktorý z .env.example vytvorí lokálny .env s náhodne vygenerovaným tajomstvom (.env sa nikdy necommituje), a zapíš to ako ADR. Testy aj alembic musia fungovať po načítaní tohto .env. Dodrž pravidlá zo sekcie 1. Po poslednom kroku FÁZY 1 sa zastav a nepokračuj bez môjho súhlasu." ;;
    1) printf '%s\n' "FÁZA 1 schválená (scripts/check_phase.sh 1 prešiel). Pokračuj FÁZOU 2 (migrácie a schéma), kroky 2.1 až 2.6 podľa docs/OPENCODE_PROMPT.md. Dodrž pravidlá zo sekcie 1, po každom kroku test a commit. Po kroku 2.6 sa zastav a nepokračuj bez môjho súhlasu." ;;
    2) printf '%s\n' "FÁZA 2 schválená (scripts/check_phase.sh 2 prešiel). Pokračuj FÁZOU 3, moduly v poradí K-16, K-01, K-02, K-05, K-04, K-03. Pre každý modul postup a) až g) zo sekcie 6, každý krok s testom a commitom, modul zaregistruj v main.py a spusti celú sadu testov. Po dokončení K-03 sa zastav a nepokračuj bez môjho súhlasu." ;;
    3) printf '%s\n' "FÁZA 3 schválená (scripts/check_phase.sh 3 prešiel). Pokračuj FÁZOU 4, moduly v poradí K-09, K-07, K-08, K-10, K-11. Pre každý modul postup a) až g) zo sekcie 6, každý krok s testom a commitom, modul zaregistruj v main.py a spusti celú sadu testov. Po dokončení K-11 sa zastav a nepokračuj bez môjho súhlasu." ;;
    4) printf '%s\n' "FÁZA 4 schválená (scripts/check_phase.sh 4 prešiel). Pokračuj FÁZOU 5, moduly v poradí K-12, K-13, K-14, K-15, K-06. Pre každý modul postup a) až g) zo sekcie 6, každý krok s testom a commitom, modul zaregistruj v main.py a spusti celú sadu testov. Po dokončení K-06 sa zastav a nepokračuj bez môjho súhlasu." ;;
    5) printf '%s\n' "FÁZA 5 schválená (scripts/check_phase.sh 5 prešiel). Pokračuj FÁZOU 6 (frontend), kroky 6.1 až 6.10. Ak chýba node alebo npm, zastav sa a nahlás to, nepreskakuj. Po kroku 6.10 sa zastav a nepokračuj bez môjho súhlasu." ;;
    6) printf '%s\n' "FÁZA 6 schválená (scripts/check_phase.sh 6 prešiel). Pokračuj FÁZOU 7 (integrácia, dokumentácia a záver), kroky 7.1 až 7.8. Report docs/REPORT_FAZA_7.md musí obsahovať skutočné výpisy a otvorené rozhodnutia bez prikrášľovania. Po kroku 7.8 sa zastav." ;;
    7) printf '%s\n' "FÁZA 7 schválená (scripts/check_phase.sh 7 prešiel). Nerob žiadne ďalšie zmeny. Vypíš iba výstup git log --oneline | head -5 a zoznam otvorených rozhodnutí z docs/REPORT_FAZA_7.md." ;;
  esac
}

N="${1:-}"
if [ "$N" = "msgs" ]; then
  for i in 0 1 2 3 4 5 6 7; do echo "=== schválenie FÁZY $i ==="; next_msg "$i"; echo; done
  echo "=== ak sa OpenCode zastavil uprostred fázy ==="
  echo "Pokračuj tam, kde si skončil, v rámci aktuálnej fázy podľa docs/OPENCODE_PROMPT.md. Najprv vypíš git log --oneline | head -5 a výsledok testov, potom pokračuj ďalším krokom. Dodrž pravidlá zo sekcie 1."
  echo
  echo "=== ak začínaš novú reláciu OpenCode ==="
  echo "Prečítaj celý docs/OPENCODE_PROMPT.md. Spusti git log --oneline | head -20 a zisti posledný dokončený krok. Pokračuj ďalším krokom v rámci tej istej fázy. Nezačínaj od začiatku a neprepisuj hotové súbory."
  exit 0
fi
case "$N" in [0-7]) ;; *) echo "Použitie: check_phase.sh <0-7> | msgs"; exit 2;; esac

cd "$ROOT" || exit 2
mkdir -p "$ROOT/.data/check"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi

FAILS=0
FAILED_LIST=""
ok()   { echo "OK            $1"; }
warn() { echo "UPOZORNENIE  $1"; }
bad()  { echo "CHYBA         $1"; FAILS=$((FAILS+1)); FAILED_LIST="${FAILED_LIST}
- $1"; }
nonempty() { if [ -s "$ROOT/$1" ]; then ok "$1"; else bad "súbor chýba alebo je prázdny: $1"; fi; }

modcheck() {
  m="${1%%:*}"; k="${1##*:}"; b="backend/app/modules/$m"
  for f in domain/models.py repository/repository.py services/service.py events/handlers.py api/router.py tests/test_service.py; do
    nonempty "$b/$f"
  done
  nonempty "docs/modules/$k.md"
  if grep -q "$m" backend/app/main.py 2>/dev/null; then ok "$m je spomenutý v main.py"; else warn "$m sa nenašiel v main.py (over registráciu modulu)"; fi
  if [ "$m" = "k16_intelligent_core" ]; then
    for p in orchestrator knowledge_system context_memory rule_system analytics_engine audit_engine; do
      nonempty "$b/$p/service.py"
    done
  fi
}

ph0() {
  nonempty docs/BASELINE.md
  nonempty .gitignore
  nonempty backend/requirements.txt
  if grep -q '^\.env$' .gitignore 2>/dev/null; then ok ".gitignore obsahuje .env"; else bad ".gitignore neobsahuje riadok .env"; fi
  if [ "$(git rev-list --count HEAD 2>/dev/null || echo 0)" -ge 1 ]; then ok "git repozitár má aspoň jeden commit"; else bad "git repozitár neexistuje alebo nemá commit"; fi
  if [ -x "$PY" ]; then ok "backend/.venv existuje"; else bad "backend/.venv chýba"; fi
  if [ -x "$PY" ] && "$PY" -c "import fastapi, sqlalchemy, alembic, pydantic, pytest, httpx" 2>/dev/null; then ok "základné závislosti sa dajú importovať"; else bad "základné závislosti sa nedajú importovať"; fi
  C=$(ls docs/adr 2>/dev/null | wc -l)
  if [ "$C" -ge 8 ]; then ok "docs/adr má $C súborov"; else warn "docs/adr má iba $C súborov (očakávaných 8 pre D1-D7 a 0001)"; fi
}
ph1() {
  for f in backend/app/core/config/settings.py backend/app/core/database/session.py backend/app/core/security/auth.py backend/app/core/security/routes.py backend/app/core/events/bus.py backend/app/core/audit/logger.py backend/app/core/permissions/policy.py backend/app/shared/types.py backend/app/shared/identity.py backend/app/shared/school.py backend/app/shared/curriculum.py backend/app/main.py .env.example; do nonempty "$f"; done
}
ph2() {
  for f in backend/alembic.ini db/migrations/env.py scripts/export_schema.py scripts/run_dev.sh; do nonempty "$f"; done
  for d in identity school curriculum learning progress teacher_workspace organization communication ai_knowledge audit; do nonempty "db/schema/$d.sql"; done
  V=$(ls db/migrations/versions/*.py 2>/dev/null | wc -l)
  if [ "$V" -ge 1 ]; then ok "migrácie vo versions: $V"; else bad "db/migrations/versions neobsahuje žiadnu migráciu"; fi
}
ph3() { for x in k16_intelligent_core:K-16 k01_learning_profile:K-01 k02_subject_workspace:K-02 k05_knowledge_continuity:K-05 k04_missions:K-04 k03_adaptive_learning:K-03; do modcheck "$x"; done; }
ph4() { for x in k09_class_overview:K-09 k07_professional_library:K-07 k08_work_assistant:K-08 k10_organization_center:K-10 k11_operations_center:K-11; do modcheck "$x"; done; }
ph5() { for x in k12_analytics_center:K-12 k13_parent_center:K-13 k14_communication_center:K-14 k15_collaboration_projects:K-15 k06_virtual_lab:K-06; do modcheck "$x"; done; }
ph6() {
  for f in frontend/package.json frontend/tsconfig.json frontend/src/app/layout.tsx frontend/src/app/page.tsx frontend/src/app/student/page.tsx frontend/src/app/teacher/page.tsx frontend/src/app/leadership/page.tsx frontend/src/app/parent/page.tsx frontend/src/lib/api.ts scripts/sync_locales.sh locales/sk/common.json locales/en/common.json; do nonempty "$f"; done
  for j in frontend/package.json locales/sk/common.json locales/en/common.json; do
    if python3 -c "import json,sys; json.load(open('$ROOT/$j'))" 2>/dev/null; then ok "platný JSON: $j"; else bad "neplatný JSON: $j"; fi
  done
  E=$(find tests/e2e frontend/tests -type f ! -name '.gitkeep' 2>/dev/null | wc -l)
  if [ "$E" -ge 1 ]; then ok "e2e alebo frontend testy: $E súborov"; else warn "žiadne e2e ani frontend testy (OpenCode to musí zdôvodniť v reporte)"; fi
}
ph7() {
  for x in k01_learning_profile:K-01 k02_subject_workspace:K-02 k03_adaptive_learning:K-03 k04_missions:K-04 k05_knowledge_continuity:K-05 k06_virtual_lab:K-06 k07_professional_library:K-07 k08_work_assistant:K-08 k09_class_overview:K-09 k10_organization_center:K-10 k11_operations_center:K-11 k12_analytics_center:K-12 k13_parent_center:K-13 k14_communication_center:K-14 k15_collaboration_projects:K-15 k16_intelligent_core:K-16; do modcheck "$x"; done
  for f in docs/REPORT_FAZA_7.md README.md scripts/seed_demo.py; do nonempty "$f"; done
  for d in api-contracts events permissions data-model; do
    X=$(find "docs/$d" -type f ! -name 'README.md' 2>/dev/null | wc -l)
    if [ "$X" -ge 1 ]; then ok "docs/$d obsahuje vygenerovaný obsah"; else warn "docs/$d obsahuje iba README.md"; fi
  done
  if git ls-files 2>/dev/null | grep -Eq '(^|/)\.env$'; then bad "súbor .env je v gite"; else ok ".env nie je v gite"; fi
  if grep -rInE "(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY)" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=.data . >/dev/null 2>&1; then bad "nájdený podozrivý reťazec tajomstva"; else ok "žiadne očividné tajomstvá"; fi
  if python3 - <<'PYEOF'
import os, sys
root = os.path.expanduser('~/KOMPAS')
skip = {'.git', '.venv', 'node_modules', '.next', '__pycache__', '.data'}
exts = ('.py', '.md', '.ts', '.tsx', '.json', '.sql', '.sh', '.txt', '.toml', '.ini', '.example', '.css')
hits = []
for d, ds, fs in os.walk(root):
    ds[:] = [x for x in ds if x not in skip]
    for f in fs:
        if f.endswith(exts):
            p = os.path.join(d, f)
            try:
                t = open(p, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if any(0x1F300 <= ord(c) <= 0x1FAFF for c in t):
                hits.append(p)
for h in hits:
    print('emoji v: ' + h)
sys.exit(1 if hits else 0)
PYEOF
  then ok "žiadne emoji"; else bad "nájdené emoji (výpis vyššie)"; fi
}

for i in $(seq 0 "$N"); do
  echo "--- kontrola súborov FÁZY $i ---"
  "ph$i"
done

if [ "$N" -ge 1 ]; then
  echo "--- syntax a testy ---"
  if [ -x "$PY" ]; then
    if find backend/app tests -name '*.py' -exec "$PY" -m py_compile {} + 2>"$ROOT/.data/check/compile.log"; then ok "py_compile všetkých .py"; else bad "py_compile zlyhal"; tail -10 "$ROOT/.data/check/compile.log"; fi
    OUT=$(cd "$ROOT/backend" && "$PY" -m pytest -q -p no:cacheprovider . ../tests 2>&1); RC=$?
    echo "$OUT" | tail -15
    if [ "$RC" -eq 0 ]; then ok "pytest prešiel"; else bad "pytest zlyhal (návratový kód $RC; 5 znamená, že sa nenašiel žiadny test)"; fi
  else
    bad "nemožno spustiť testy, chýba backend/.venv"
  fi
fi

if [ "$N" -ge 2 ] && [ -x "$PY" ]; then
  echo "--- cyklus migrácií ---"
  TMPDB="$ROOT/.data/check/migr_check.db"; rm -f "$TMPDB"
  LOG="$ROOT/.data/check/alembic.log"
  if ( cd "$ROOT/backend" && export DATABASE_URL="sqlite:///$TMPDB" && "$PY" -m alembic upgrade head && "$PY" -m alembic downgrade base && "$PY" -m alembic upgrade head ) >"$LOG" 2>&1; then ok "alembic upgrade, downgrade, upgrade"; else bad "alembic cyklus zlyhal"; tail -15 "$LOG"; fi
  rm -f "$TMPDB"
fi

if [ "$N" -ge 6 ]; then
  echo "--- build frontendu ---"
  LOG="$ROOT/.data/check/npm_build.log"
  if command -v npm >/dev/null 2>&1; then
    if ( cd "$ROOT/frontend" && npm run build ) >"$LOG" 2>&1; then ok "npm run build"; else bad "npm run build zlyhal"; tail -15 "$LOG"; fi
  else
    bad "npm nie je nainštalovaný"
  fi
fi

echo "--- stav gitu ---"
git log --oneline 2>/dev/null | head -5
if [ -n "$(git status --short 2>/dev/null)" ]; then warn "pracovný strom má necommitnuté zmeny"; fi

echo
if [ "$FAILS" -eq 0 ]; then
  echo "VÝSLEDOK: FÁZA $N je v poriadku, môžeš schváliť."
  echo "----- VLOŽ DO OPENCODE -----"
  next_msg "$N"
else
  echo "VÝSLEDOK: FÁZA $N NIE JE v poriadku, počet chýb: $FAILS."
  echo "----- VLOŽ DO OPENCODE -----"
  echo "FÁZA $N neschválená. Nezávislá kontrola scripts/check_phase.sh $N našla tieto chyby:${FAILED_LIST}"
  echo "Oprav presne tieto chyby, po každej oprave spusti testy a pošli nový report. Testy neoslabuj ani nemaž, aby prešli. Nepokračuj do ďalšej fázy."
fi
