#!/usr/bin/env bash
# Obnoví zálohu do samostatnej testovacej databázy, porovná počty riadkov
# a overí hash reťazec audit_log. Exit kód 0 iba ak všetko prejde.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PGDATA="${PGDATA:-$ROOT/.data/pg}"
export PGPORT="${PGPORT:-55432}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGUSER="${PGUSER:-kompas}"
export PGDATABASE="${PGDATABASE:-kompas}"
RESTORE_DB="${RESTORE_DB:-kompas_restore_test}"

if [ -s "$ROOT/.data/pg_password" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$(cat "$ROOT/.data/pg_password")"
fi
if [ -z "${PGPASSWORD:-}" ]; then
  echo "CHYBA: chýba PGPASSWORD alebo .data/pg_password" >&2
  exit 2
fi

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
  BACKUP_FILE="$(ls -1t "$ROOT/.data/backups"/*.dump 2>/dev/null | head -n1 || true)"
fi
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Záloha neexistuje, vytváram novú..." >&2
  bash "$ROOT/scripts/db_backup.sh"
  BACKUP_FILE="$(ls -1t "$ROOT/.data/backups"/*.dump | head -n1)"
fi
echo "Používam zálohu: $BACKUP_FILE"

# zastaviť starú testovaciu DB
PGPASSWORD="$PGPASSWORD" dropdb --if-exists --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" "$RESTORE_DB" >/dev/null 2>&1 || true
PGPASSWORD="$PGPASSWORD" createdb --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" "$RESTORE_DB"

pg_restore --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" \
  --dbname="$RESTORE_DB" --no-owner --no-acl --clean --if-exists "$BACKUP_FILE" >"$ROOT/.data/check/restore.log" 2>&1 || {
    cat "$ROOT/.data/check/restore.log" >&2
    exit 1
  }

# porovnanie počtov riadkov
TABLES="$(psql --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" --dbname="$PGDATABASE" -Atc \
  "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")"

MISMATCH=0
for t in $TABLES; do
  SRC=$(psql --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" --dbname="$PGDATABASE" -Atc "SELECT count(*) FROM \"$t\"")
  DST=$(psql --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" --dbname="$RESTORE_DB" -Atc "SELECT count(*) FROM \"$t\"")
  if [ "$SRC" != "$DST" ]; then
    echo "NESPRAVNÝ POČET: $t source=$SRC restored=$DST" >&2
    MISMATCH=1
  fi
done
if [ "$MISMATCH" -ne 0 ]; then
  echo "CHYBA: počty riadkov sa líšia" >&2
  exit 1
fi
echo "Počty riadkov zhodné pre všetky tabuľky."

# overenie hash reťazca
export DATABASE_URL="postgresql+pg8000://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${RESTORE_DB}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-test-secret-key-0123456789abcdef}"
export JWT_ALGORITHM=HS256
export PYTHONPATH="$ROOT/backend"
VERIFY_OUT="$("$ROOT/backend/.venv/bin/python" - <<'PY'
import os
os.environ.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])
from app.core.database.session import SessionLocal
from app.core.audit.logger import verify_chain
db = SessionLocal()
try:
    ok, bad = verify_chain(db)
    print(f"verify_chain: ok={ok} bad_id={bad}")
    raise SystemExit(0 if ok else 1)
finally:
    db.close()
PY
)"
echo "$VERIFY_OUT"
echo "Obnova a overenie prebehli úspešne."
