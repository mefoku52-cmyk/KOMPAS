#!/usr/bin/env bash
# Starts the KOMPAS backend on 127.0.0.1:8000 in the background.
set -a
. /data/data/com.termux/files/home/KOMPAS/.env
set +a
export PYTHONPATH=/data/data/com.termux/files/home/KOMPAS/backend
cd /data/data/com.termux/files/home/KOMPAS
exec /data/data/com.termux/files/home/KOMPAS/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
