# KOMPAS

Inteligentny partner skoly pre ziaka, ucitela, vedenie skoly a rodica. Projekt je v aktivnom vyvoji (modularny monolit: backend FastAPI + SQLAlchemy, frontend planovany).

## Predpoklady

- Python 3.14+ (overene v prostredi projektu)
- Virtualne prostredie backendu: `backend/.venv`
- Nastroj Node.js a npm (potrebne pre frontend, Faza 6)

## Nastavenie prostredia

1. Vytvor lokalny `.env` s nahodnym tajomstvom (subor sa necommituje):

```bash
bash scripts/make_env.sh
```

2. Skontroluj/aktivuj backend zavislosti vo virtualnom prostredi `backend/.venv` (verzie su pripnute v `backend/requirements.txt`).

## Spustenie backendu

```bash
bash scripts/run_dev.sh
```

- Server bezi na porte `APP_PORT` (predvolene 8000).
- Kontrola stavu: `GET /health`
- Prihlasenie: `POST /auth/login`

Pred spustenim musia byt nastavene premenne prostredia (napr. cez `.env`): `DATABASE_URL`, `JWT_SECRET_KEY` (HS256, bez predvolenej hodnoty).

## Migracie (Alembic)

Migracie su v `db/migrations`, konfiguracia v `backend/alembic.ini`.

```bash
cd backend
set -a; . ../.env; set +a
export PYTHONPATH=.
../backend/.venv/bin/python -m alembic upgrade head
```

Iné operacie: `alembic downgrade base`, opätovný `alembic upgrade head`.

## Generovanie schemy

Subory `db/schema/*.sql` su generovane exporty DDL pre PostgreSQL (D2):

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/export_schema.py
```

## Testy

Backend a integracne testy (zo korena repozitara, s načítanym `.env`):

```bash
set -a; . ./.env; set +a
PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend
```

Kontrolny skript fazy:

```bash
bash scripts/check_phase.sh <cislo_fazy>
```

## Frontend

Frontend (Next.js) bude doplneny vo Faze 6. Preklady: zdroj pravdy `locales/`, synchronizacia do `frontend/src/locales` skriptom `scripts/sync_locales.sh` (bude doplnene).

## Demonštračné dáta

Skript `scripts/seed_demo.py` bude doplneny v neskoršej faze. Demonštračné dáta musia byt oznacene `is_demo = true`.

## Dokumentacia

- Zakladny stav prostredia a rozhodnutia: `docs/BASELINE.md`
- Architektonicke rozhodnutia (ADR): `docs/adr/`
