#!/usr/bin/env bash
set -u
cd "$HOME/KOMPAS/backend" || exit 2
. .venv/bin/activate || { echo "CHYBA: chýba backend/.venv"; exit 2; }

if ! command -v cargo >/dev/null 2>&1; then
  echo "Inštalujem rust a binutils cez pkg"
  pkg install -y rust binutils || { echo "CHYBA: pkg install rust zlyhal"; exit 3; }
fi
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
export CARGO_BUILD_JOBS=2
echo "ANDROID_API_LEVEL=$ANDROID_API_LEVEL"
echo "cargo: $(cargo --version 2>&1)"

FAILED=""
for p in pydantic pydantic-settings fastapi uvicorn sqlalchemy alembic httpx pytest PyJWT argon2-cffi; do
  echo "=== $p ==="
  if pip install "$p"; then echo "VYSLEDOK $p OK"; else echo "VYSLEDOK $p ZLYHAL"; FAILED="$FAILED $p"; fi
done

echo
python -c "import fastapi, sqlalchemy, alembic, pydantic, pytest, httpx, jwt, argon2; print('core ok')" 2>&1
if [ -n "$FAILED" ]; then echo "ZLYHALI:$FAILED"; else echo "VSETKO NAINSTALOVANE"; fi
echo "KONIEC SKRIPTU"
