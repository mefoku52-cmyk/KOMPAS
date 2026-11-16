# ADR 0003 - D2: Migracie a export schemy

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Schema sa musi dat verzovat, migrovat a zverejnit v citatelnej podobe pre PostgreSQL.

## Rozhodnutie
- Migracie sa riadia cez Alembic s adresarom `db/migrations`.
- Subory `db/schema/*.sql` su generovane exporty DDL pre PostgreSQL (skript `scripts/export_schema.py`), nie rucne pisane.

## Dosledky
- Zmeny schemy vznikaju cez nove migracie; stare migracie sa neupravuju.
- SQL exporty sa generuju zo stavu modelov/migracii a sluzia ako dokumentacia a kontrola.
