# K18 Intelligence Layer — integrácia v KOMPAS

## Stav

- Modul: `backend/app/modules/k18_intelligence/` (FastAPI routery, SQLAlchemy modely, orchestrátor, safety, outbox/inbox simulácia).
- DB: `il_*` tabuľky cez Alembic `f202ec1baf80` + `b7a0d74fa430`.
- Event: subscribuje `AnswerEvaluated` (bus) a spracúva cez `IntelligenceOrchestrator`; zachovaná kompatibilita s K17.
- Frontend: student/teacher/leadership zobrazujú K18 notifikácie/situácie/report (feature-presence cez existujúce API volania, bezpečné fallbacky).

## API (hlavné)

- `GET /intelligence/status`
- `POST /intelligence/events`
- `GET /intelligence/situations`, `GET /intelligence/situations/{entity_id}`
- `POST /intelligence/situations/{initiative_id}/dismiss|approve`
- `GET /intelligence/notifications`, `POST /intelligence/notifications/{id}/acknowledge`
- `GET /intelligence/audit` (leadership)
- `GET /intelligence/admin/config|health|entities` (leadership)
- `GET /intelligence/report/system` (leadership)
- `POST /intelligence/ops/outbox/enqueue`, `POST /intelligence/ops/process-once`, `GET /intelligence/ops/queues` (leadership)
- `POST /integration/events`, `/integration/students/{id}/summary`, `/integration/teachers/{id}/overview`, `/integration/health`
- `GET /simulation/flow?entity_id=...`

## Bezpečnosť / pravidlá

- Deterministické kritické rozhodnutia v safety/reasoning vrstvách; predikcie sú hypotézy s neistotou.
- Neutrálne texty pre žiaka/rodiča; žiadne skóre/diagnózy.
- RBAC: leadership-only admin/audit/report/ops; student/parent len vlastná entita/notifikácie; teacher approve/dismiss podľa roly. Plné TEACHES_CLASS/GUARDIAN_OF scoping je ďalej potrebné doplniť v rámci `app.core.permissions.policy` kontextov.
- Idempotencia: `event_id` dedup v `il_perception_event` + outbox/inbox.
- Audit: kľúčové akcie zapisované do `il_audit`.

## Dev DB poznámka (Termux/existujúca DB)

Ak `.data/kompas.db` už obsahuje `il_*` tabuľky, ale `alembic_version` je starší (napr. `818426796485`), **nepúšťaj blind upgrade**. Over:

```bash
PYTHONPATH=backend backend/.venv/bin/python - <<'PY'
import sqlite3
c=sqlite3.connect('.data/kompas.db')
print(c.execute("select version_num from alembic_version").fetchall())
print([r[0] for r in c.execute("select name from sqlite_master where type='table' and name like 'il_%'").fetchall()])
PY
```

Ak sú `il_*` tabuľky kompletné a zodpovedajú migráciám, použite `alembic stamp b7a0d74fa430` (po zálohe DB). Ak chýbajú, použite `alembic upgrade head`.

## Otvorené otázky

- Q1 K-04 time/errors kontrakt — UNKNOWN.
- Q5 retencia 365 dní — UNKNOWN/compliance.
- Q6 hodnotové jadro — UNKNOWN.
- Q2 K-16 rozšíriť vs K-18 — PROPOSED.
- Produkčná infra/reálne mobilné testovanie — BLOCKED.
