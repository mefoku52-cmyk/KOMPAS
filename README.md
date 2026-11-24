# KOMPAS

Inteligentný partner školy pre žiaka, učiteľa, vedenie školy a rodiča (modulárny monolit: backend FastAPI + SQLAlchemy, frontend Next.js).

Demonštračné údaje v tomto repozitári sú ilustračné a musia byť označené `is_demo = true` (pozri `scripts/seed_demo.py`). Otvorené rozhodnutia a stav sú v `docs/REPORT_FAZA_7.md`.

## Predpoklady

- Python 3.14+ a virtuálne prostredie `backend/.venv` (závislosti v `backend/requirements.txt`)
- Node.js a npm (frontend; v Termux/Android overené s workaroundom v 6.9)
- Git

## Nastavenie prostredia

1. Vytvor lokálny `.env` s náhodným tajomstvom (súbor sa necommituje):

```bash
bash scripts/make_env.sh
```

2. Pred príkazmi načítaj premenné (príklad):

```bash
set -a; . ./.env; set +a
```

Povinné premenné: `DATABASE_URL`, `JWT_SECRET_KEY` (HS256, bez predvolenej hodnoty). Voliteľné: `APP_PORT`, `GRADE_MIN`, `GRADE_MAX` (dočasné technické predvolené hodnoty), `ANALYTICS_MIN_GROUP_SIZE`.

## Spustenie backendu

Jeden príkaz (načíta `.env` ak existuje, spustí uvicorn):

```bash
bash scripts/run_dev.sh
```

- Server: `http://0.0.0.0:${APP_PORT:-8000}`
- Stav: `GET /health`
- Prihlásenie: `POST /auth/login`

## Migrácie (Alembic)

Migrácie: `db/migrations` (konfigurácia `backend/alembic.ini`).

```bash
cd backend
set -a; . ../.env; set +a
export PYTHONPATH=.
../backend/.venv/bin/python -m alembic upgrade head
```

Cyklus kontroly: `alembic upgrade head`, `alembic downgrade base`, `alembic upgrade head` (na čistej databáze).

## Generovanie schémy

`db/schema/*.sql` sú generované exporty DDL pre PostgreSQL (D2), podľa prefixov oblastí (D3):

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/export_schema.py
```

## Testy

Backend a integračné testy (z koreňa repozitára, s `.env`):

```bash
set -a; . ./.env; set +a
PYTHONPATH=backend backend/.venv/bin/python -m pytest -q -p no:cacheprovider backend
```

Kontrola fázy:

```bash
bash scripts/check_phase.sh <0-7>
```

## Frontend

Next.js (TypeScript, App Router) v `frontend/`. Preklady: zdroj pravdy `locales/` (sk predvolené, en), synchronizácia:

```bash
bash scripts/sync_locales.sh
```

Vývoj:

```bash
cd frontend
npm run dev
```

Zostavenie (produkčný build):

```bash
cd frontend
npm run build
```

Poznámka k prostrediu: pre Termux/Android je zachovaný Babel fallback (`frontend/.babelrc` + `@babel/runtime`), pretože natívny SWC pre `android-arm64` nemusí byť dostupný. Lokálny vývojový server otvoríš na `http://127.0.0.1:3000` po spustení `npm run dev` v `frontend/`. Ak potrebuješ prihlásenie a dáta, spusti aj backend na porte 8000 cez `bash scripts/run_dev.sh` z koreňa. e2e testy (Playwright) v tomto prostredí nemusia byť spustiteľné (chýbajú browser binárky); detail a alternatívy sú v `docs/REPORT_FAZA_7.md`.

## Demonštračné dáta (seed)

Skript vytvára ilustračné dáta označené `is_demo = true` (bez skutočných osôb):

```bash
set -a; . ./.env; set +a
PYTHONPATH=backend backend/.venv/bin/python scripts/seed_demo.py
```

## Dokumentácia

- Záverečný report a otvorené rozhodnutia: `docs/REPORT_FAZA_7.md`
- Základný stav a rozhodnutia: `docs/BASELINE.md`, `docs/adr/`
- Moduly: `docs/modules/K-01.md` až `K-16.md`
- API kontrakty (generované): `docs/api-contracts/README.md`, `docs/api-contracts/openapi.json`
- Udalosti (generované): `docs/events/README.md`
- Oprávnenia a matica: `docs/permissions/README.md`
- Dátový model (generované): `docs/data-model/README.md`
