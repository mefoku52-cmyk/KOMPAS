# PROGRES - produkčná etapa (FÁZY 8–16)

| Fáza | Krok | Stav | Commit | Dátum | Poznámka |
|---|---|---|---|---|---|
| 0 | - | hotové | 516722a | 2026-11-16 | Audit a základ (etapa 1, schválené) |
| 1 | - | hotové | 516722a | 2026-11-16 | Jadro backendu (etapa 1, schválené) |
| 2 | - | hotové | 516722a | 2026-11-16 | Migrácie a schéma (etapa 1, schválené) |
| 3 | - | hotové | 516722a | 2026-11-16 | Moduly skupina A (etapa 1, schválené) |
| 4 | - | hotové | 516722a | 2026-11-16 | Moduly skupina B (etapa 1, schválené) |
| 5 | - | hotové | 516722a | 2026-11-16 | Moduly skupina C (etapa 1, schválené) |
| 6 | - | hotové | 516722a | 2026-11-16 | Frontend (etapa 1, schválené) |
| 7 | - | hotové | 516722a | 2026-11-16 | Integrácia, dokumentácia a záver (etapa 1, schválené) |
| 8 | 8.1 | hotové | 72e280a | 2026-11-16 | Vytvorený PROGRES.md, FÁZY 0–7 označené ako hotové |
| 8 | 8.2 | hotové | 9793660 | 2026-11-16 | Inventár 341 súborov do PRODUKCIA_AUDIT.md |
| 8 | 8.3 | hotové | 43f2857 | 2026-11-16 | Porovnanie modulov K-01..K-16 so sekciou 7 a docs/modules |
| 8 | 8.4 | hotové | 19d2a0c | 2026-11-16 | scripts/check_contract.py (frontend vs OpenAPI), zoznam modulov bez UI volania |
| 8 | 8.5 | hotové | b7ca4f0 | 2026-11-16 | scripts/flow_smoke.py HTTP smoke (login+status+negatíva), doménové medzery ako GAP |
| 8 | 8.6 | hotové | d8bb72b | 2026-11-16 | docs/FLOW.md (skutočný priebeh, HTTP vs service, medzery) |
| 8 | 8.7 | hotové | d8bb72b | 2026-11-16 | docs/PRODUKCIA_ROZHODNUTIA.md (otvorené body/rozhodnutia) |
| 8 | 8.8 | hotové | d8bb72b | 2026-11-16 | Aktualizácia PROGRES a kontrola FÁZY 8 (check_prod 8, čiastočný beh) |
| 9 | 9.1 | hotové | 5da770f | 2026-11-17 | Doménové HTTP endpointy K-01..K-16, spoločné API utility, jednotné chyby, auth na statusoch |
| 9 | 9.2 | hotové | 126be42 | 2026-11-17 | Testy jednotného formátu chýb, request_id a mapovania výnimiek |
| 9 | 9.3 | hotové | ee458fa | 2026-11-17 | Stránkovanie, filtre a horné limity zoznamov overené testami |
| 9 | 9.4 | hotové | 7c53cc0 | 2026-11-17 | In-memory rate limiter, prísnejší login limit a konfigurácia |
| 9 | 9.5 | hotové | 901c58c | 2026-11-17 | JWT expirácia/issuer/audience, logout revocation, zmena hesla, politika a lockout |
| 9 | 9.6 | hotové | 8ee0b34 | 2026-11-17 | scripts/manage.py: školy, používatelia, heslá, deaktivácia, rollover, export auditu |
| 9 | 9.7 | hotové | 2e86467 | 2026-11-17 | Prechod roka: nové triedy/ročníky, história, idempotencia, absolventi podľa GRADE_MAX |
| 9 | 9.8 | hotové | 7fa553c | 2026-11-17 | Export údajov žiaka JSON s povinným účelom, rolami a auditom; anonymizácia iba ADR |
| 9 | 9.9 | hotové | 52e2e37 | 2026-11-17 | Overený šablónový režim K-08 a deterministický NullProvider K-16; externí poskytovatelia iba zakázaná konfigurácia |
| 9 | 9.10 | hotové | 4b842dc | 2026-11-17 | Plná sada 115 testov, alembic upgrade/downgrade/upgrade, N1 self-match opravený, storage abstraktný |
| 10 | 10.1 | hotové | f2b91a3 | 2026-11-17 | Overené PostgreSQL 18.6, pg_dump, Redis 8.10.3; pg8000 a redis klient nainštalované |
| 10 | 10.2 | hotové | 84a615e | 2026-11-17 | scripts/pg_dev.sh init/start/stop/status v .data/pg, heslom cez env/súbor; status overený |
| 10 | 10.3 | hotové | 7f083bc | 2026-11-17 | Alembic upgrade head na PostgreSQL 18.6 prešiel všetkými migráciami; pg8000 driver |
| 10 | 10.4 | hotové | 365dc9e | 2026-11-17 | scripts/test_pg.sh: plná sada 115 testov proti PostgreSQL zelená; odložené FK a test fixture |
| 10 | 10.5 | hotové | 14cc869 | 2026-11-17 | EXPLAIN na 8 000 žiakoch/80 000 stavoch/50 000 auditoch; 15 zložených indexov, CHECK roly a nezáporných pokusov |
| 10 | 10.6 | hotové | 76b88cc | 2026-11-17 | DB_POOL_* a DB_STATEMENT_TIMEOUT_MS z env; QueuePool pre PostgreSQL, statement_timeout cez startup_params |
