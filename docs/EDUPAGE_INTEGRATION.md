# EduPage / SIS integrácia (K19)

## Stav implementácie

- **Implementované v kóde (MVP, SIS-agnostické):** integračný modul `backend/app/modules/k19_sis_integration`, tabuľky `sis_source`, `sis_identity_map`, `sis_sync_job`, `sis_sync_item`, šifrované uloženie API kľúča (Fernet odvodeny zo `SIS_SECRET_KEY` alebo fallback `JWT_SECRET_KEY`), leadership-only admin API, dry-run/full sync, audit logovanie, CLI príkazy v `scripts/manage.py`, základný admin UI v leadership dashboarde.
- **EduPage provider:** oficiálny HTTP adapter `eduapi` s `Authorization: Bearer <API key>` a príkazom `getbasedata` (`format=json`). Normalizuje učiteľov, žiakov, triedy, školské roky, zápisy, priradenia učiteľ-trieda a rodič-dieťa linky, ak sú v payloade prítomné.
- **Neimplementované/limitované:** plná delta synchronizácia podľa EduPage kurzora (fallback na full snapshot), write-back do EduPage, automatická deaktivácia pri absencii v N behoch (MVP hlási kandidátov), rodičia/stravovanie/rozvrh/známky ako doménový sync, produkčný scheduler.

## Bezpečnosť

- API kľúč sa nevracia v API odpovediach; uložený je šifrovane v `sis_source.encrypted_secret`.
- RBAC: iba `LEADERSHIP` v rovnakej škole alebo system principal cez CLI.
- Audit: `sis.source.create/update/test`, `sis.sync.started/finished`, `sis.user.created`, `sis.enrollment.changed`, `sis.sync.completed`.
- Izolácia škôl: všetky dotazy viazané na `school_id` a `source_id`.
- Žiadne hard-delete identít; deaktivácia sa nerobí automaticky bez politiky.

## Potrebné externé podklady (blokery na produkčné nasadenie)

1. **EduPage admin prístup školy** na vytvorenie API kľúča a pridelenie minimálnych práv (min. čítanie základných dát/`getbasedata`).
2. **Subdoména školy** (`<subdomain>.edupage.org`) a potvrdený base URL.
3. **Anonymizovaný vzor reálneho payloadu** `getbasedata` pre danú školu (polia pre rodičov, statusy, school year, class teacher väzby sa medzi inštaláciami líšia).
4. **Rozhodnutia**: source-of-truth polia, grace period pre odchod žiaka, pravidlo pre generovanie username, či sa majú rodičia importovať automaticky.
5. **GDPR/DPIA**: právny základ, zmluvné vzťahy, retencia sync logov, prístupové roly.

## Konfigurácia

- `SIS_SYNC_ENABLED=false` - globálny feature flag.
- `SIS_SYNC_INTERVAL_MINUTES=30` - plánovaný interval (min. 5).
- `SIS_MIN_POLL_SECONDS=300` - ochranný limit voči EduPage.
- `SIS_REQUEST_TIMEOUT_SECONDS=30`.
- `SIS_DEACTIVATE_ABSENT_AFTER_RUNS=3` - pripravené pre budúcu politiku.
- `SIS_ALLOW_WRITE_BACK=false` - write-back je blokovaný.
- `SIS_SECRET_KEY` - odporúčané; inak fallback na `JWT_SECRET_KEY`.

## Admin API

- `GET /integrations/sis/status`
- `GET /integrations/sis/sources?school_id=`
- `POST /integrations/sis/sources`
- `PATCH /integrations/sis/sources/{source_id}`
- `POST /integrations/sis/sources/{source_id}/test`
- `POST /integrations/sis/sources/{source_id}/sync` body `{ "mode": "dry_run"|"full" }`
- `GET /integrations/sis/jobs`

## CLI

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/manage.py sis-add-source --school-id <uuid> --provider edupage --name "EduPage" --subdomain skola --api-key-env EDUPAGE_API_KEY --enabled
PYTHONPATH=backend backend/.venv/bin/python scripts/manage.py sis-list-sources --school-id <uuid>
PYTHONPATH=backend backend/.venv/bin/python scripts/manage.py sis-test --school-id <uuid> --source-id <uuid>
PYTHONPATH=backend backend/.venv/bin/python scripts/manage.py sis-sync --school-id <uuid> --source-id <uuid> --mode dry_run
```

## Mapovanie

- EduPage teacher/student/guardian -> `identity_user` + `identity_role_assignment`; externý ID v `sis_identity_map`.
- EduPage class -> `school_class_group`.
- EduPage school year -> `school_year`.
- Student class assignment -> `school_enrollment` (zmena triedy aktualizuje enrollment pre daný školský rok).
- Teacher-class assignment -> `school_class_teacher`.
- Guardian-child -> `identity_guardian_link`.

## Prevádzkové limity

- EduPage oficiálna API má obmedzenia a môže blokovať pri zneužití; polling držať >= 300s.
- Integrácia je navrhnutá ako adaptér; ďalší SIS sa pridá implementáciou `SISProvider` a normalizera.
- Pred zapnutím na produkčnej DB spraviť zálohu a migráciu na kópii. Táto implementácia nepridáva automatický scheduler do app startupu.
