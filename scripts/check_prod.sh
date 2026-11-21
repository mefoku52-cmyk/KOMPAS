#!/usr/bin/env bash
# Použitie: bash ~/KOMPAS/scripts/check_prod.sh <8-16>
ROOT="$HOME/KOMPAS"
PY="$ROOT/backend/.venv/bin/python"
N="${1:-}"
case "$N" in 8|9|10|11|12|13|14|15|16) ;; *) echo "Použitie: check_prod.sh <8-16>"; exit 2;; esac
cd "$ROOT" || exit 2
mkdir -p "$ROOT/.data/check"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi

FAILS=0; FAILED_LIST=""
ok()   { echo "OK            $1"; }
warn() { echo "UPOZORNENIE  $1"; }
bad()  { echo "CHYBA         $1"; FAILS=$((FAILS+1)); FAILED_LIST="${FAILED_LIST}
- $1"; }
nonempty() { if [ -s "$ROOT/$1" ]; then ok "$1"; else bad "súbor chýba alebo je prázdny: $1"; fi; }
lines_ge() { c=$(wc -l < "$ROOT/$1" 2>/dev/null || echo 0); if [ "$c" -ge "$2" ]; then ok "$1 ($c riadkov)"; else bad "$1 má $c riadkov, očakávaných aspoň $2"; fi; }
runcheck() { # popis, príkaz...
  d="$1"; shift
  LOG="$ROOT/.data/check/run.log"
  if "$@" >"$LOG" 2>&1; then ok "$d"; else bad "$d zlyhal (posledné riadky nižšie)"; tail -15 "$LOG"; fi
}
npm_has() { "$PY" -c "import json,sys; sys.exit(0 if '$1' in json.load(open('$ROOT/frontend/package.json')).get('scripts',{}) else 1)" 2>/dev/null; }

ph8()  { for f in docs/PROGRES.md docs/PRODUKCIA_AUDIT.md docs/FLOW.md docs/PRODUKCIA_ROZHODNUTIA.md scripts/check_contract.py scripts/flow_smoke.py; do nonempty "$f"; done; lines_ge docs/PRODUKCIA_AUDIT.md 40; lines_ge docs/FLOW.md 30; lines_ge docs/PRODUKCIA_ROZHODNUTIA.md 15; }
ph9()  { for f in backend/app/core/errors.py backend/app/core/ratelimit.py scripts/manage.py backend/tests/test_rollover.py backend/tests/test_errors_ratelimit.py; do nonempty "$f"; done; }
ph10() { for f in scripts/pg_dev.sh scripts/test_pg.sh scripts/db_backup.sh scripts/db_restore_test.sh; do nonempty "$f"; done; lines_ge docs/DATABAZA.md 20; }
ph11() { for f in scripts/audit_deps.sh backend/tests/test_security.py; do nonempty "$f"; done; lines_ge docs/THREAT_MODEL.md 30; lines_ge docs/SECURITY.md 30; }
ph12() {
  for f in frontend/src/styles/tokens.css frontend/src/lib/i18n.ts scripts/check_locales.py frontend/src/app/error.tsx frontend/src/app/not-found.tsx frontend/src/app/loading.tsx; do nonempty "$f"; done
  for c in Tile TileGrid StatCard KnowledgeBar Icon DataTable Modal Toast EmptyState ErrorBoundary Skeleton NavShell LanguageSwitcher; do nonempty "frontend/src/components/$c.tsx"; done
}
ph13() {
  for r in student teacher leadership parent; do lines_ge "frontend/src/app/$r/page.tsx" 60; done
  T=$(find frontend -path frontend/node_modules -prune -o -type f \( -name '*.test.ts' -o -name '*.test.tsx' -o -name '*.spec.ts' -o -name '*.spec.tsx' \) -print 2>/dev/null | wc -l)
  if [ "$T" -ge 5 ]; then ok "frontend testy: $T súborov"; else bad "frontend testy: iba $T súborov (očakávaných aspoň 5)"; fi
}
ph14() {
  for f in backend/app/core/observability.py scripts/run_prod.sh backend/Dockerfile frontend/Dockerfile docker-compose.yml infra/docker/nginx.conf .env.production.example .dockerignore scripts/validate_infra.sh scripts/ci.sh; do nonempty "$f"; done
  lines_ge docs/PREVADZKA.md 25
}
ph15() { for f in scripts/loadtest.py scripts/e2e_api.py; do nonempty "$f"; done; lines_ge docs/KVALITA.md 30; }
ph16() { for f in scripts/smoke_prod.sh; do nonempty "$f"; done; for f in RUNBOOK DEPLOY_PRODUKCIA PRED_PRODUKCIOU REPORT_PRODUKCIA; do lines_ge "docs/$f.md" 30; done; }

for i in $(seq 8 "$N"); do echo "--- kontrola súborov FÁZY $i ---"; "ph$i"; done

echo "--- bezpečnosť a čistota ---"
if git ls-files 2>/dev/null | grep -Eq '(^|/)\.env$'; then bad "súbor .env je v gite"; else ok ".env nie je v gite"; fi
if grep -rInE "(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY)" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=.data . >/dev/null 2>&1; then bad "nájdený podozrivý reťazec tajomstva"; else ok "žiadne očividné tajomstvá"; fi
if "$PY" - <<'PYEOF'
import os, sys
root = os.path.expanduser('~/KOMPAS')
skip = {'.git', '.venv', 'node_modules', '.next', '__pycache__', '.data'}
exts = ('.py', '.md', '.ts', '.tsx', '.json', '.sql', '.sh', '.txt', '.toml', '.ini', '.css', '.yml', '.yaml', '.conf', '.example')
hits = []
for d, ds, fs in os.walk(root):
    ds[:] = [x for x in ds if x not in skip]
    for f in fs:
        if f.endswith(exts) or f in ('Dockerfile', '.dockerignore'):
            try:
                t = open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if any(0x1F300 <= ord(c) <= 0x1FAFF for c in t):
                hits.append(os.path.join(d, f))
for h in hits:
    print('emoji v: ' + h)
sys.exit(1 if hits else 0)
PYEOF
then ok "žiadne emoji"; else bad "nájdené emoji (výpis vyššie)"; fi

echo "--- kontrola placeholderov (pravidlo N1) ---"
PLOUT=$("$PY" - <<'PYEOF'
import ast, os, re, sys
root = os.path.expanduser('~/KOMPAS')
dirs = ['backend/app', 'backend/tests', 'scripts', 'frontend/src', 'db/schema']
skip = {'__pycache__', 'node_modules', '.next', '.venv', 'versions'}
findings = []
kw = re.compile(r'\b(TO' + 'DO|FIX' + 'ME)\b|lo' + 'rem ipsum|co' + 'ming soon|pripra' + 'vuje sa', re.I)
def is_exempt_class(node):
    for b in node.bases:
        name = getattr(b, 'id', None) or getattr(b, 'attr', None) or ''
        if name in ('Protocol', 'ABC'):
            return True
    return False
def only_stub(body):
    stmts = list(body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(getattr(stmts[0], 'value', None), ast.Constant) and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    if not stmts:
        return True
    for s in stmts:
        if isinstance(s, ast.Pass):
            continue
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis:
            continue
        if isinstance(s, ast.Raise) and s.exc is not None:
            e = s.exc.func if isinstance(s.exc, ast.Call) else s.exc
            if getattr(e, 'id', '') == 'NotImplementedError':
                continue
        return False
    return True
for base in dirs:
    p0 = os.path.join(root, base)
    for d, ds, fs in os.walk(p0):
        ds[:] = [x for x in ds if x not in skip]
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            if f in ('.gitkeep', '__init__.py'):
                continue
            size = os.path.getsize(p)
            if size == 0:
                findings.append('prázdny súbor: ' + rel); continue
            ext = os.path.splitext(f)[1]
            try:
                text = open(p, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if ext in ('.py', '.ts', '.tsx', '.css', '.sh') and kw.search(text):
                findings.append('TO' 'DO/FIX' 'ME alebo zástupný text: ' + rel)
            if ext == '.tsx' and size < 120:
                findings.append('podozrivo malý TSX komponent (' + str(size) + ' B): ' + rel)
            if ext == '.py':
                try:
                    tree = ast.parse(text)
                except SyntaxError:
                    findings.append('syntaktická chyba: ' + rel); continue
                exempt = set()
                for n in ast.walk(tree):
                    if isinstance(n, ast.ClassDef) and is_exempt_class(n):
                        for m in ast.walk(n):
                            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                exempt.add(id(m))
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and id(n) not in exempt:
                        decos = ' '.join(ast.unparse(x) for x in n.decorator_list)
                        if 'abstractmethod' in decos or 'overload' in decos:
                            continue
                        if only_stub(n.body):
                            findings.append('prázdne telo funkcie ' + n.name + ': ' + rel + ':' + str(n.lineno))
for x in findings:
    print(x)
sys.exit(1 if findings else 0)
PYEOF
); PLRC=$?
echo "$PLOUT" | head -40
if [ "$PLRC" -eq 0 ]; then ok "žiadne placeholdery"; else
  CNT=$(echo "$PLOUT" | grep -c .)
  if [ "$N" -eq 8 ]; then warn "nájdených placeholderov: $CNT (FÁZA 8 iba zaznamenáva, oprava vo FÁZE 9)"; else bad "nájdené placeholdery ($CNT), výpis vyššie"; fi
fi

echo "--- backend: syntax, testy, migrácie ---"
if [ -x "$PY" ]; then
  if find backend/app backend/tests scripts -name '*.py' -exec "$PY" -m py_compile {} + 2>"$ROOT/.data/check/compile.log"; then ok "py_compile všetkých .py"; else bad "py_compile zlyhal"; tail -8 "$ROOT/.data/check/compile.log"; fi
  OUT=$(cd "$ROOT/backend" && "$PY" -m pytest -q -p no:cacheprovider . ../tests 2>&1); RC=$?
  echo "$OUT" | tail -8
  if [ "$RC" -eq 0 ]; then ok "pytest (SQLite) prešiel"; else bad "pytest zlyhal (kód $RC)"; fi
  TMPDB="$ROOT/.data/check/migr.db"; rm -f "$TMPDB"
  if ( cd "$ROOT/backend" && export DATABASE_URL="sqlite:///$TMPDB" && "$PY" -m alembic upgrade head && "$PY" -m alembic downgrade base && "$PY" -m alembic upgrade head ) >"$ROOT/.data/check/alembic.log" 2>&1; then ok "alembic upgrade, downgrade, upgrade"; else bad "alembic cyklus zlyhal"; tail -12 "$ROOT/.data/check/alembic.log"; fi
  rm -f "$TMPDB"
else
  bad "chýba backend/.venv"
fi

[ "$N" -ge 8 ]  && [ -f scripts/check_contract.py ] && runcheck "scripts/check_contract.py (frontend verzus OpenAPI)" "$PY" scripts/check_contract.py
[ "$N" -ge 8 ]  && [ -f scripts/flow_smoke.py ]    && runcheck "scripts/flow_smoke.py (celý tok cez HTTP)" "$PY" scripts/flow_smoke.py
[ "$N" -ge 10 ] && [ -f scripts/test_pg.sh ]       && runcheck "scripts/test_pg.sh (backend sada na PostgreSQL)" bash scripts/test_pg.sh
[ "$N" -ge 10 ] && [ -f scripts/db_restore_test.sh ] && runcheck "scripts/db_restore_test.sh (záloha a obnova)" bash scripts/db_restore_test.sh
[ "$N" -ge 12 ] && [ -f scripts/check_locales.py ] && runcheck "scripts/check_locales.py (sk a en)" "$PY" scripts/check_locales.py

echo "--- všetky shell skripty: bash -n ---"
SHFAIL=0
for f in $(find scripts -name '*.sh' 2>/dev/null); do bash -n "$f" 2>/dev/null || { bad "bash -n zlyhal: $f"; SHFAIL=1; }; done
[ "$SHFAIL" -eq 0 ] && ok "bash -n pre všetky .sh"

if [ "$N" -ge 12 ]; then
  echo "--- frontend ---"
  if command -v npm >/dev/null 2>&1; then
    for s in typecheck test; do
      if npm_has "$s"; then runcheck "npm run $s" bash -c "cd '$ROOT/frontend' && npm run $s"; else bad "chýba npm skript: $s"; fi
    done
    if [ "$N" -ge 13 ]; then
      if npm_has build; then runcheck "npm run build" bash -c "cd '$ROOT/frontend' && npm run build"; else bad "chýba npm skript: build"; fi
    fi
    if npm_has lint; then runcheck "npm run lint" bash -c "cd '$ROOT/frontend' && npm run lint"; else warn "npm skript lint nie je definovaný"; fi
  else
    bad "npm nie je nainštalovaný"
  fi
fi

if [ "$N" -ge 14 ] && [ -f scripts/validate_infra.sh ]; then
  echo "--- infraštruktúra ---"
  runcheck "scripts/validate_infra.sh" bash scripts/validate_infra.sh
  if grep -q 'NEOVERENE V TOMTO PROSTREDI' docs/*.md 2>/dev/null; then ok "docs označujú neoverené časti"; else warn "docs neobsahujú označenie NEOVERENE V TOMTO PROSTREDI (over, či sa Docker skutočne testoval)"; fi
fi

if [ "$N" -ge 16 ]; then
  echo "--- záverečný beh ---"
  [ -f scripts/smoke_prod.sh ] && runcheck "scripts/smoke_prod.sh (produkčný profil)" bash scripts/smoke_prod.sh
  [ -f scripts/ci.sh ] && runcheck "scripts/ci.sh" bash scripts/ci.sh
  [ -f scripts/check_phase.sh ] && runcheck "regresia scripts/check_phase.sh 7" bash scripts/check_phase.sh 7
fi

echo "--- stav gitu ---"
git log --oneline 2>/dev/null | head -5
if [ -n "$(git status --short 2>/dev/null)" ]; then warn "pracovný strom má necommitnuté zmeny"; fi

echo
if [ "$FAILS" -eq 0 ]; then
  echo "VÝSLEDOK: FÁZA $N je v poriadku, môžeš schváliť."
  if [ "$N" -eq 8 ]; then echo "PRED SCHVÁLENÍM: otvor docs/PRODUKCIA_ROZHODNUTIA.md, prečítaj predvolené hodnoty P1 až P8 a ak chceš iné, pripíš ich do správy nižšie."; fi
  echo "----- VLOŽ DO OPENCODE -----"
  if [ "$N" -lt 16 ]; then
    M=$((N+1))
    echo "FÁZA $N schválená (scripts/check_prod.sh $N prešiel). Pokračuj FÁZOU $M podľa docs/OPENCODE_PROMPT_PRODUKCIA.md, všetky jej kroky po sebe. Medzi krokmi sa nezastavuj. Aktualizuj docs/PROGRES.md po každom kroku. Dlhé príkazy spúšťaj cez nohup s logom. Po poslednom kroku napíš presne vetu: FÁZA $M DOKONČENÁ - ČAKÁM NA SCHVÁLENIE a zastav sa."
  else
    echo "FÁZA 16 schválená. Nerob žiadne ďalšie zmeny ani nasadenie. Vypíš git log --oneline | head -5 a zoznam bodov z docs/PRED_PRODUKCIOU.md, ktoré sú stále otvorené."
  fi
else
  echo "VÝSLEDOK: FÁZA $N NIE JE v poriadku, počet chýb: $FAILS."
  echo "----- VLOŽ DO OPENCODE -----"
  echo "FÁZA $N neschválená. Nezávislá kontrola scripts/check_prod.sh $N našla tieto chyby:${FAILED_LIST}"
  echo "Oprav presne tieto chyby, po každej oprave spusti testy a pošli nový report. Testy neoslabuj ani nemaž, aby prešli, a placeholdery nenahrádzaj inými placeholdermi. Aktualizuj docs/PROGRES.md. Po oprave napíš presne vetu: FÁZA $N DOKONČENÁ - ČAKÁM NA SCHVÁLENIE a zastav sa."
fi
