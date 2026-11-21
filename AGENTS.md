# KOMPAS — poznámky pre agenta

Modulárny monolit: **backend FastAPI + SQLAlchemy** (`backend/app`, 16 modulov k01–k16) a
**frontend Next.js 13.5 App Router** (`frontend/src`). Doména: školský „kompas" pre žiaka,
učiteľa, vedenie a rodiča. Demo dáta majú `is_demo = true`.

## Spustenie (Termux, overené 2026-11-18)

Backend (port 8000, načíta `.env`, SQLite `.data/kompas.db`):
```bash
setsid -f bash scripts/dev_backend.sh > .data/logs/backend.log 2>&1
```
Frontend (dev, port 3000):
```bash
cd ~/KOMPAS/frontend && setsid -f bash -c 'node node_modules/next/dist/bin/next dev -p 3000 -H 127.0.0.1' > ../.data/logs/web.log 2>&1
```
POZOR: `pkill -f "uvicorn app.main"` zabije vlastný shell (cmdline obsahuje hľadaný
reťazec) → používaj bracket trik `pkill -f "[u]vicorn app.main"`.

## Demo prístup

`demo_student` / `demo_teacher` / `demo_leadership` / `demo_parent`, heslo `demo-password`
(seed: `scripts/seed_demo.py`, idempotentný: `create_base()` + `create_content()`, škola `81985a0a…`).
Login: `POST /auth/login {username,password}` → JWT; frontend si rolu parsuje z tokenu.

## Stav UI vs API (2026-11-18, po napojení)

- Backend: **85 rout** v 16 moduloch; `/docs` + `/openapi.json` zapnuté mimo produkcie
  (`APP_DOCS_ENABLED`, inak automaticky v `APP_ENV != production`).
- Frontend je **napojený na API** (žiadne natvrdo zadané ID):
  - `/student`: K01 profil, K05 stavy (počítadlá + najnovší stav na tému), K03 odporúčania,
    K04 misie → úlohy → odovzdanie odpovede (POST /k04/attempts), história pokusov.
  - `/teacher`: K09 triedy učiteľa + prehľad stavov, K07 knižnica (aj pridanie materiálu),
    K08 koncepty (vytvorenie + odoslanie na schválenie).
  - `/leadership`: K12 analytics (s potlačením malých skupín), K10 plány/úlohy, K11 požiadavky
    s povolenými prechodmi stavov.
  - `/parent`: K13 dieťa (meno + agregovaný pokrok, bez súkromných poznámok), K14 vlákna a správy.
- Nové/zmenené endpointy pre UI: `GET /k09/classes` (triedy učiteľa), `GET /k01/profiles/{id}/latest`
  už nevyžaduje `school_year_id` (doplní z enrollmentu), `/k04/attempts/mine` vracia `task_prompt`,
  K13 overview vracia `child_full_name`, K14 správy `sender_full_name`, `/k05/states/{id}` vracia `topic_name`.

## K05 stav učiva (2026-11-18) — pravidlo, ktoré musíš dodržať

`progress_topic_state` je **append-only** (každá odpoveď pridá riadok). Preto sa "stav témy" NIKDY
nepočíta ako najnovší riadok. Spoločné pravidlo = `backend/app/shared/progress.py::resolve_effective_states`:
- **precvičovanie** môže stav zvýšiť (`in_progress_practice` → `partially_mastered`), ale nikdy ho nezníži
  (jeden zlý pokus nezruší zvládnutie),
- **overenie** platí vždy, aj keď zlyhá (neúspešné overenie reálne zníži `verified_mastery`).
Toto pravidlo používajú K03, K09, K12, K13 a frontend (`frontend/src/lib/progress.ts` — rovnaká logika).
`status_value()` normalizuje veľkosť písmen: SQLAlchemy ukladá MENÁ enumov (`VERIFIED_MASTERY`),
API serializuje HODNOTY (`verified_mastery`) — bez normalizácie čítania ticho zlyhávajú.

Pozor: `by_status` v K09/K12/K13 je odteraz s malými písmenami (predtým enum mená) — frontend
na tom staval `Status.STATUS_LABELS`, dovtedy rolové stránky ukazovali nuly.

Čísla v prehľade žiaka: prebraté/precvičované/čiastočné/overené sú **témy**, nie pokusy; aby bolo
vidieť aktivitu, pribudli „Odovzdané odpovede" a „Úspešnosť" + hláška po každom odovzdaní
(čo sa zmenilo / čo zostalo). „Moje pokusy" ukazuje najnovších 5 (API radí `valid_from DESC`).

Numerické úlohy akceptujú desatinnú **čiarku** (`0,75` = `0.75`), viď `_normalise_number` v
`k04_missions/services/service.py`.

## Príkazy

- Testy: `set -a; . ./.env; set +a; PYTHONPATH=backend backend/.venv/bin/python -m pytest -q -p no:cacheprovider backend`
- Fáza: `bash scripts/check_phase.sh <0-7>`; schéma: `scripts/export_schema.py`
- Build frontendu (Termux workaround): `cd frontend && npm run build` (Babel fallback, `swcMinify:false`)

## Poznámky / pitfally

- `/tmp` v Termuxe nie je zapisovateľný → `$TMPDIR`.
- `.env.local` vo frontende: `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000`.
- Prvý `next dev` kompiluje stránku 25–50 s (Babel) — curl s dlhým timeoutom.
- Repo obsahuje viacero `.bak` DB a `PROMPT.txt` (scratch, necommitovať).
