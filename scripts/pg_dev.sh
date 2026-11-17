#!/usr/bin/env bash
# Lokálna vývojová PostgreSQL inštancia pre KOMPAS.
# Použitie: scripts/pg_dev.sh init|start|stop|status
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PGDATA="${PGDATA:-$ROOT/.data/pg}"
PGPORT="${PGPORT:-55432}"
PGHOST="${PGHOST:-127.0.0.1}"
PGUSER="${PGUSER:-kompas}"
PGDATABASE="${PGDATABASE:-kompas}"
PASSWORD_FILE="${PGPASSWORD_FILE:-$ROOT/.data/pg_password}"

command -v initdb >/dev/null || { echo "CHYBA: initdb chýba" >&2; exit 1; }
command -v pg_ctl >/dev/null || { echo "CHYBA: pg_ctl chýba" >&2; exit 1; }
command -v psql >/dev/null || { echo "CHYBA: psql chýba" >&2; exit 1; }

is_running() {
  [ -f "$PGDATA/PG_VERSION" ] && pg_ctl -D "$PGDATA" status >/dev/null 2>&1
}

load_password() {
  if [ -n "${PGPASSWORD:-}" ]; then
    return 0
  fi
  if [ -s "$PASSWORD_FILE" ]; then
    PGPASSWORD="$(cat "$PASSWORD_FILE")"
  else
    PGPASSWORD="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)"
    umask 077
    printf '%s\n' "$PGPASSWORD" > "$PASSWORD_FILE"
    chmod 600 "$PASSWORD_FILE"
  fi
  export PGPASSWORD
}

ensure_database() {
  load_password
  local exists
  exists="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = '$PGDATABASE'")"
  if [ "$exists" != "1" ]; then
    createdb -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE"
    echo "Vytvorená databáza $PGDATABASE"
  fi
}

cmd_init() {
  mkdir -p "$PGDATA"
  chmod 700 "$PGDATA"
  if [ -f "$PGDATA/PG_VERSION" ]; then
    echo "Inštancia už existuje: $PGDATA"
    return 0
  fi
  load_password
  local pwfile
  pwfile="$(mktemp "$PGDATA.pw.XXXXXX")"
  chmod 600 "$pwfile"
  printf '%s\n' "$PGPASSWORD" > "$pwfile"
  initdb -D "$PGDATA" -U "$PGUSER" --pwfile="$pwfile" \
    --auth-local=trust --auth-host=scram-sha-256 --encoding=UTF8 --no-instructions
  rm -f "$pwfile"
  echo "Inicializovaná inštancia: $PGDATA"
}

cmd_start() {
  if ! [ -f "$PGDATA/PG_VERSION" ]; then
    echo "CHYBA: najprv spusti scripts/pg_dev.sh init" >&2
    exit 1
  fi
  if is_running; then
    echo "Inštancia už beží na $PGHOST:$PGPORT"
  else
    mkdir -p "$PGDATA"
    pg_ctl -D "$PGDATA" -l "$PGDATA/server.log" \
      -o "-p $PGPORT -h $PGHOST" -w start
  fi
  ensure_database
  echo "PostgreSQL beží na $PGHOST:$PGPORT, databáza $PGDATABASE"
}

cmd_stop() {
  if is_running; then
    pg_ctl -D "$PGDATA" -m fast -w stop
    echo "PostgreSQL zastavený"
  else
    echo "PostgreSQL nebeží"
  fi
}

cmd_status() {
  if ! [ -f "$PGDATA/PG_VERSION" ]; then
    echo "Stav: neinicializovaná ($PGDATA)"
    exit 1
  fi
  if is_running; then
    load_password
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -tAc "SELECT version()" | sed 's/^/Stav: beží | /'
  else
    echo "Stav: zastavená ($PGDATA)"
    exit 1
  fi
}

case "${1:-}" in
  init) cmd_init ;;
  start) cmd_start ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  *) echo "Použitie: $0 init|start|stop|status" >&2; exit 2 ;;
esac
