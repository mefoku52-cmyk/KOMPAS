#!/usr/bin/env bash
# Vytvorí logickú zálohu lokálnej PostgreSQL databázy pomocou pg_dump.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PGDATA="${PGDATA:-$ROOT/.data/pg}"
export PGPORT="${PGPORT:-55432}"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGUSER="${PGUSER:-kompas}"
export PGDATABASE="${PGDATABASE:-kompas}"

if [ -s "$ROOT/.data/pg_password" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$(cat "$ROOT/.data/pg_password")"
fi
if [ -z "${PGPASSWORD:-}" ]; then
  echo "CHYBA: chýba PGPASSWORD alebo .data/pg_password" >&2
  exit 2
fi

BACKUP_DIR="${BACKUP_DIR:-$ROOT/.data/backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="${1:-$BACKUP_DIR/${PGDATABASE}_${STAMP}.dump}"

pg_dump --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" \
  --format=custom --no-owner --no-acl --file="$OUT" "$PGDATABASE"

echo "Záloha vytvorená: $OUT"
