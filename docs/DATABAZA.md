# Databáza KOMPAS

Dokument pokrýva lokálny vývoj, PostgreSQL, Redis, migrácie, zálohovanie a obnovu.
Produkčné predvolené hodnoty sú v `docs/PRODUKCIA_ROZHODNUTIA.md`; nič v tomto dokumente
nepredstavuje nasadenie do externého prostredia (pravidlo N7).

## Dostupnosť nástrojov v tomto prostredí (FÁZA 10)

Overené v Termuxe dňa 2026-11-17:

| Nástroj | Verzia | Stav |
|---|---|---|
| postgres | 18.6 | dostupný v PATH |
| initdb | 18.6 | dostupný v PATH |
| pg_ctl | 18.6 | dostupný v PATH |
| psql | 18.6 | dostupný v PATH |
| pg_dump | 18.6 | dostupný v PATH |
| createdb / dropdb | 18.6 | dostupné v PATH |
| redis-server | 8.10.3 | dostupný v PATH |
| redis-cli | 8.10.3 | dostupný v PATH |
| Python (venv) | 3.14.8 | backend a testy |

Doplnené Python knižnice bez kompilácie: `pg8000` (čistý Python driver pre SQLAlchemy)
a `redis` (čistý Python klient). `psql` CLI v Termuxe funguje; `sqlite3` CLI nie je potrebné.

## Lokálna PostgreSQL inštancia

Lokálna vývojová inštancia sa spravuje cez `scripts/pg_dev.sh` a žije v `.data/pg`.
Heslo sa ukladá do `.data/pg_password` (mód 600, mimo gitu) alebo sa zadá cez `PGPASSWORD`.
Príkazy:

```bash
export PGPASSWORD='...'          # heslo sa neukladá do gitu
bash scripts/pg_dev.sh init       # initdb, ak ešte neexistuje
bash scripts/pg_dev.sh start
bash scripts/pg_dev.sh status
bash scripts/pg_dev.sh stop
```

Predvolené parametre: `PGDATA=.data/pg`, `PGPORT=55432`, `PGUSER=kompas`,
`PGDATABASE=kompas`, host `127.0.0.1`. Všetky sa dajú prepísať premennými prostredia.

## Migrácie

Alembic sa spúšťa z adresára `backend`:

```bash
cd backend
DATABASE_URL='postgresql+pg8000://kompas:...@127.0.0.1:55432/kompas' \
  .venv/bin/python -m alembic upgrade head
```

Schéma sa nesmie meniť úpravou starých migrácií; každá zmena je nový súbor v
`db/migrations/versions`. SQLite zostáva predvolená pre rýchly vývoj, PostgreSQL je
cieľová produkčná databáza (D1).
