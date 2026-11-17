#!/usr/bin/env bash
# Spustí celú backend testovaciu sadu proti lokálnemu PostgreSQL.
# Exit kód je exit kód pytestu. Ak inštancia nebeží, script ju spustí cez pg_dev.sh.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/backend/.venv/bin/python"
export PGDATA="${PGDATA:-$ROOT/.data/pg}"
export PGPORT="${PGPORT:-55432}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGUSER="${PGUSER:-kompas}"
export PGDATABASE="${PGDATABASE:-kompas_test}"

if [ -s "$ROOT/.data/pg_password" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$(cat "$ROOT/.data/pg_password")"
fi
if [ -z "${PGPASSWORD:-}" ]; then
  echo "CHYBA: chýba PGPASSWORD alebo .data/pg_password" >&2
  exit 2
fi

bash "$ROOT/scripts/pg_dev.sh" start || exit $?
export KOMPAS_TEST_DATABASE_URL="postgresql+pg8000://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}"
export DATABASE_URL="$KOMPAS_TEST_DATABASE_URL"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-test-secret-key-0123456789abcdef}"
export JWT_ALGORITHM=HS256
export PYTHONPATH="$ROOT/backend"

echo "PostgreSQL test DB: $PGHOST:$PGPORT/$PGDATABASE"
cd "$ROOT/backend" || exit 2
"$PY" -m alembic upgrade head
ALEMBIC_RC=$?
if [ "$ALEMBIC_RC" -ne 0 ]; then
  echo "CHYBA: alembic upgrade head zlyhal ($ALEMBIC_RC)" >&2
  exit "$ALEMBIC_RC"
fi
"$PY" -m pytest -q -p no:cacheprovider . ../tests
exit $?
