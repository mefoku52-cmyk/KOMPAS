# REPORT FÁZA 7 (integrácia, dokumentácia a záver)

Stav k poslednému commitu: `d37bcaa F7.7: disable public docs/openapi endpoints, keep only /health and auth public` (pracovný strom čistý pred vytvorením tohto reportu). Všetky nižšie výpisy sú skutočné výstupy z terminálu v tomto prostredí.

## 7.1 Integračný test hlavného toku

**Cieľ:** žiak rieši úlohu -> vyhodnotenie (K-04) -> uloženie stavu (K-05 cez udalosť) -> analytika/agregáty (K-12), triedny prehľad učiteľa (K-09), osobný pokrok žiaka (K-05), doplňujúce precvičovanie/odporúčanie (K-03), platná auditná reťaz.

**Súbor:** `backend/tests/test_integration_main_flow.py`
**Spustenie:**
```
$ PYTHONPATH=backend backend/.venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_integration_main_flow.py
.                                                                        [100%]
1 passed in 2.06s
---RC=0---
```
**Overené v teste:** pokus vyhodnotený (`is_correct=True, evaluated=True`), publikovaná udalosť `AnswerEvaluated` -> K-05 handler zapísal stav `practiced/partially_mastered` (nie `verified_mastery` pri precvičovaní), K-03 vrátil deterministické vysvetliteľné odporúčanie (`reason` obsahuje "Deterministic", `suggested_action=practice`), K-09 triedny prehľad pre priradeného učiteľa (`total_students=5`), K-12 agregát školy nepotlačený pri >=5, `verify_chain(db_session)` -> `(True, None)`.

**Regresia opravená počas kroku:** prvé behy zlyhali na nesprávnom asertovaní návratovej hodnoty `verify_chain` (vracia `(ok, bad_id)`) a na umiestnení testu mimo `backend/` (fixture `db_session`); test presunutý do `backend/tests/`, asercia opravená, následne zelený. Žiadne testy neboli oslabené ani mazané.

## 7.2 Matica oprávnení

**Súbory:** `docs/permissions/README.md` (zdroj pravdy matice), `backend/tests/test_permissions_matrix.py`
**Spustenie:**
```
$ PYTHONPATH=backend backend/.venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_permissions_matrix.py
.................                                                        [100%]
17 passed in 23.72s
---RC=0---
```
**Pokrytie (dvojice rola-zdroj/akcia-kontext vrátane zamietnutí):** SELF povolené/zamietnuté (cudzí), GUARDIAN_OF povolené/zamietnuté (bez väzby), TEACHES_CLASS povolené/zamietnuté (nepriradený učiteľ), SCHOOL_AGGREGATE povolené (vedenie) / zamietnuté (žiak), SCHOOL_INDIVIDUAL_WITH_PURPOSE povolené s účelom / zamietnuté bez účelu, TEACHER_PRIVATE_NOTE povolené vlastníkovi / zamietnuté rodičovi a žiakovi, PARENT_PRIVATE_COMMUNICATION povolené účastníkovi / zamietnuté neúčastníkovi, TEACHES_CLASS zamietnuté pre neroli učiteľa, bez kontextu -> deny-by-default.

**Úprava testu počas kroku:** jeden negatívny prípad TEACHES_CLASS mal v kontexte nesprávne nastavené `teacher_user_id` voči očakávaniu (policy vyhodnotila podľa poskytnutého kontextu inak), prípad bol opravený tak, aby korektne vyjadroval „nepriradený učiteľ“ a očakával zamietnutie; logika policy ani iné testy neboli oslabené.

## 7.3 Overenie auditu

**Overenie v integračnom teste (7.1):**
```
ok, bad_id = verify_chain(db_session)
assert ok is True
assert bad_id is None
```
(výsledok behu 7.1: `1 passed`).

**Overenie na aktuálnej databáze prostredia (`DATABASE_URL`):**
```
$ PYTHONPATH=backend backend/.venv/bin/python - <<'PY' ... verify_chain ...
DB sqlite:///./.data/kompas.db
VERIFY True None
---RC=0---
```
```
(True, None)
---VERIFY_END---
```
Auditná reťaz (`audit_log`, hashované prepojenie, append-only v core) je po integračnom toku platná.

## 7.4 Demonštračné dáta (seed)

**Súbor:** `scripts/seed_demo.py` (spustiteľný). Dáta sú ilustračné, bez skutočných osôb, všetky relevantné záznamy `is_demo=true`.

**Spustenie na čistej testovacej DB:**
```
$ DATABASE_URL="sqlite:///<...>/.data/check/seed_test.db" PYTHONPATH=backend backend/.venv/bin/python scripts/seed_demo.py
DEMO dáta vytvorené (ilustračné, is_demo=true).
school_id=d187b952-a23e-49dd-8c72-6229b289429a school_year_id=960574da-3097-48aa-8289-4b1c18fcb831 class_id=44802b03-91a6-4d52-a75a-c41aa70d2da3 topic_id=285057a8-bc34-4cd7-8ba4-ee15755c5a64
Používatelia (heslo: demo-password):
  - student: demo_student (DEMO Žiak)
  - teacher: demo_teacher (DEMO Učiteľ)
  - leadership: demo_leadership (DEMO Vedenie)
  - parent: demo_parent (DEMO Rodič)
UPOZORNENIE: Tieto údaje sú iba demonštračné a nepredstavujú skutočné osoby.
---RC=0---
```
(opakovaný beh: `---RC=0---` so seed súborom `seed_report.db` vytvoril DEMO dáta rovnako, `is_demo=true`).

## 7.5 Generovanie dokumentácie

**Skript:** `scripts/generate_docs.py`
**Spustenie:**
```
$ PYTHONPATH=backend backend/.venv/bin/python scripts/generate_docs.py
generated api-contracts/events/data-model
---RC=0---
```
**Výstupy:**
- `docs/api-contracts/openapi.json`, `docs/api-contracts/README.md` (generované z OpenAPI schémy aplikácie)
```
$ head -n 12 docs/api-contracts/README.md
# API kontrakty

Generované z OpenAPI (`app.openapi()`). Zdroj: `docs/api-contracts/openapi.json`.

## Endpointy

- `POST /auth/login` - Login (tagy: auth, security v schéme: nie (verejné alebo nešpecifikované v schéme))
- `GET /health` - Health (tagy: -, security v schéme: nie (verejné alebo nešpecifikované v schéme))
- `GET /k01/status` - Status (tagy: k01, security v schéme: nie (verejné alebo nešpecifikované v schéme))
...
```
- `docs/events/README.md` (katalóg): infra `EventBus`/`DomainEvent`/`audit_event_log`, publikované/odoberané `AnswerEvaluated` / `learning.answer_evaluated` (K-04 -> K-05), ostatné bez doménových publikácií v aktuálnom rozsahu.
- `docs/permissions/README.md` - matica oprávnení (zdroj pre 7.2, vyplnená).
- `docs/data-model/README.md` - generované z SQLAlchemy metadata, tabuľky podľa oblastí/prefixov (D3) vrátane stĺpcov.

## 7.6 README

**Súbor:** `README.md` (aktualizovaný) - obsahuje: nastavenie prostredia/`.env`, spustenie backendu jedným príkazom `bash scripts/run_dev.sh`, migrácie Alembic, generovanie schémy, testy, kontrolu fáz, frontend (sync locales, dev, build + poznámka k prostrediu), seed demo dát, odkazy na dokumentáciu.

## 7.7 Bezpečnostná kontrola

- **Tajomstvá v gite:** `.env` nie je v gite; sken podozrivých reťazcov bez nálezov.
```
---SECRET_SCAN---
---ENDSECRET---
---ENV_IN_GIT---
none
---ENDENV---
```
- **Endpointy bez autentifikácie:** verejne vystavené ostali iba `/health` a `/auth/*` (prihlásenie); OpenAPI/docs/redoc endpointy boli vypnuté (`docs_url=None, redoc_url=None, openapi_url=None`).
```
$ PYTHONPATH=backend backend/.venv/bin/python - <<'PY' (výpis app.routes)
ROUTES
/health ['GET']
 []
 ...
END
---RC=0---
```
- **Deny-by-default:** overené automatickými testami matice (17 passed, vrátane „bez kontextu -> deny_by_default“) a existujúcimi testami oprávnení v moduloch; `authorize` predvolene zamieta.

**Zmena počas 7.7:** vypnutie verejných docs endpointov FastAPI (kompatibilné s požiadavkou „žiadne endpointy bez autentifikácie okrem /health a prihlásenia“); generovanie OpenAPI pre dokumentáciu prebieha v procese cez `get_openapi` nad `app.routes` (`scripts/generate_docs.py`).

## 7.8 Čo funguje, čo nie, čo zostáva (bez prikrášľovania)

**Funguje (s dôkazmi):**
- Backend jadro, moduly K-16, K-01..K-05, K-07..K-15, K-06 registrované v `main.py`, migrácie (16 verzií) a generovaná schéma podľa oblastí.
- Hlavný integračný tok (úloha->vyhodnotenie->udalosť->stav kontinuity->odporúčanie->triedny prehľad->agregát) prechádza (`1 passed`), auditná reťaz platná po toku aj na DB (`(True, None)`).
- Matica oprávnení podľa `docs/permissions/README.md` automaticky overená (`17 passed`), deny-by-default.
- Celá backend testovacia sada: `75 passed in 112.08s (0:01:52) ---RC=0---`.
- Migrácie: cyklus `alembic upgrade head, downgrade base, upgrade head` prešiel v kontrolách fáz (OK v `scripts/check_phase.sh 6` logu aj v priebehu fázy 7).
- Seed demo dát `is_demo=true` funguje (RC 0).
- Generovaná dokumentácia: `docs/api-contracts/*`, `docs/events/README.md`, `docs/data-model/README.md`, matica oprávnení.
- Frontend (Next.js TS, App Router, sk/en locales, role pages, API klient s 401/403) sa zostavuje: `npm run build` -> `✓ Compiled successfully`, `✓ Generating static pages (8/8)` (RC 0, Termux workaround 6.9).
- Bezpečnosť: `.env` mimo gitu, žiadne zjavné tajomstvá v skene, verejné endpointy obmedzené na `/health` a auth.

**Čo nefunguje / obmedzenia:**
- **E2E (Playwright, 6.10):** nespustené v tomto prostredí. Dôvod: `tests/e2e/.gitkeep`, `frontend/tests/.gitkeep` (žiadne e2e testy/konfigurácia), Playwright a natívne browser binárky nie sú v Termux/Android dostupné. Alternatívy: (1) doplniť a spustiť Playwright na podporovanom prostredí/CI proti bežiacemu backendu+frontendu, (2) rozšíriť API/integračné scenáre rolí cez pytest+httpx, (3) frontend smoke testy (Testing Library) bez natívnych prehliadačov ak sú závislosti kompatibilné. Potichu nepreskočené.
- **Frontend produkčný build v natívnom SWC režime na Android/arm64:** natívny SWC balík nebol dostupný (`@next/swc-android-arm64` 404 / „Failed to load SWC binary for android/arm64“ pri Next 14.2.35; WASM fallback v danom nastavení nenačítal). Funkčná oprava: Next 13.5.x + `.babelrc` (`next/babel`) + `swcMinify:false`, build skript cez lokálny `next`. To je environment workaround, nie plnohodnotná náhrada natívneho SWC; na podporovanej platforme odporúčané overiť natívny build.
- **OpenAPI/Swagger UI endpointy:** zámerne vypnuté z dôvodu 7.7 (bez neautentifikovaných endpointov okrem /health a prihlásenia); dokumentačný `openapi.json` je generovaný skriptom.
- `scripts/check_phase.sh 7` počas tejto relácie reportoval aj upozornenia, že `docs/events`, `docs/permissions`, `docs/data-model` „obsahuje iba README.md“ (skript hodnotí prítomnosť ďalších súborov než README) - samotné README sú však vygenerované a vyplnené (nie prázdne).

**Čo zostáva / ďalšie kroky (návrh):** spustiť e2e na CI/podporovanej platforme; overiť frontend build/deploy mimo Termux; prípadne zapnúť chránenú (autentifikovanú) dokumentáciu API ak bude potrebná; rozšíriť integračný tok o UI/e2e naprieč rolami.

## Otvorené rozhodnutia (bez prikrášľovania)

1. **GRADE_MIN / GRADE_MAX** - technická predvolená hodnota 1 a 9 (konfigurácia), dočasná kým používateľ nerozhodne.
2. **Zariadenia/priorita** - frontend responzívny (telefón/tablet/počítač/interaktívna tabuľa), bez rozhodnutia o prioritách.
3. **AI architektúra (hybrid/lokál/cloud)** - implementované rozhranie `ModelProvider` a deterministický `NullProvider` (bez siete), žiadny API kľúč, žiadne údaje o žiakoch externému poskytovateľovi bez povolenia `rule_system`; konkrétni poskytovatelia/nasadenie nerozhodnuté.
4. **Nasadenie (samostatná inštancia/centrálna/hybrid)** - `school_id` vo všetkých dátach súvisiacich so školou, rozhodnutie o nasadení neurobené.
5. **E2E testy** - nástroj/alternatíva a prostredie na spustenie (Playwright vs iné) zostáva otvorené.
6. **Frontend build toolchain na cieľovej platforme** - natívny SWC vs Babel fallback podľa cieľa nasadenia (aktuálne riešené workaroundom pre Termux).

## Výpisy - súhrnné dôkazy

**Git stav a história (po 7.7):**
```
$ git --no-pager log --oneline -10
d37bcaa F7.7: disable public docs/openapi endpoints, keep only /health and auth public
d96e836 F7.6: update README with run, tests, migrations, seed and frontend instructions
813406b F7.5: generate api contracts, events catalog and data model docs
3f87366 F7.4: add demo seed script with is_demo data
75304cd F7.2: add permissions matrix doc and automated matrix tests
3548c1e F7.1 fix: correct audit chain verification in integration flow test
ec1d5db F7.1: add integration test for main event flow
5230d59 F6.9 fix: make frontend build pass on Termux (next 13, babel fallback)
3f65f96 F6.4-6.8: responsive layout, login/role redirect and role pages
b2b99a9 F7.3: API client with token handling and 401/403 behavior
---STATUS---
(cistý)
```

**Backend testy (celá sada):**
```
$ PYTHONPATH=backend backend/.venv/bin/python -m pytest -q -p no:cacheprovider backend
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 112.08s (0:01:52)
---RC=0---
```

**Kontrola fázy 6 (log, prechod):** `OK pytest prešiel`, `OK alembic upgrade, downgrade, upgrade`, `OK npm run build`, `VÝSLEDOK: FÁZA 6 je v poriadku, môžeš schváliť.`

**Verejné trasy po 7.7:** iba `GET /health`; ostatné moduly registrované bez verejných docs endpointov.
