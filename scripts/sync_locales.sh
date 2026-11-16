#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/locales"
DST="$ROOT/frontend/src/locales"
mkdir -p "$DST"
rm -rf "$DST"/*
cp -R "$SRC"/. "$DST"/
echo "synced locales -> $DST"
