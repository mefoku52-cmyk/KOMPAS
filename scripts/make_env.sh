#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="$ROOT_DIR/.env.example"
TARGET="$ROOT_DIR/.env"

if [ ! -f "$EXAMPLE" ]; then
  echo "CHYBA: .env.example neexistuje: $EXAMPLE" >&2
  exit 1
fi

if [ -f "$TARGET" ]; then
  echo "CHYBA: .env uz existuje: $TARGET (neprepisujem)" >&2
  exit 1
fi

SECRET="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    JWT_SECRET_KEY=*)
      printf 'JWT_SECRET_KEY=%s\n' "$SECRET" >> "$tmp"
      ;;
    *)
      printf '%s\n' "$line" >> "$tmp"
      ;;
  esac
done < "$EXAMPLE"

cp "$tmp" "$TARGET"
chmod 600 "$TARGET" 2>/dev/null || true
echo "Vytvorene: $TARGET"
