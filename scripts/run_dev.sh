#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a
fi

: "${APP_PORT:=8000}"
export PYTHONPATH="$ROOT_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"

cd "$ROOT_DIR/backend"
exec "$ROOT_DIR/backend/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT" --reload
