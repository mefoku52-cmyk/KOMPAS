# BASELINE - KOMPAS (Faza 0)

Datum: 2026-11-16
Stav: Faza 0 dokoncena (0.1-0.6), caka sa na schvalenie Fazy 1.

## 1. Prostredie (krok 0.1)

- Operacny system/prostredie: Linux v Termuxe na Androide (pracovny adresar projektu: ~/KOMPAS).
- Python: 3.14.8
- pip (systemovy): 26.2.2 (`/data/data/com.termux/files/usr/lib/python3.14/site-packages/pip`)
- Node.js: v24.22.2
- npm: 12.2.1
- git: 2.56.0
- sqlite3 (CLI): NEDOSTUPNE - binarka `/data/data/com.termux/files/home/android-sdk/platform-tools/sqlite3` nie je spustitelna (`cannot execute binary file: Exec format error`). SQLite ako kniznica v Pythone je dostupna.
- psql (PostgreSQL): 18.6 (klient)
- redis-server: 8.10.3
- docker: v24.0.6-ce (v Termuxe pravdepodobne nefunkcny na realne kontajnery; `infra/` zostava zastupna podla zadania)

Poznamka k prikazom: prikazy, ktore mozu trvat viac ako 30 sekund, sa maju spustat na pozadi cez `nohup` s logom (nie s timeout 30). Instalacia zavislosti bola vykonana na pozadi mimo tejto relacie (skript `scripts/install_deps.sh`).

## 2. Kontrola kostry (krok 0.2)

- Celkovy pocet suborov: 305
- Pocet `.py` suborov pod `backend/app/modules`: 221 (ocakavane: 221) - OK
- Pocet poloziek v `backend/app/modules`: 18 (16 modulov + `__init__.py` + `__pycache__`) - OK
- Adresare kostry pritomne: backend, frontend, db, docs, tests, locales, scripts, infra
- Zoznam modulov: k01_learning_profile, k02_subject_workspace, k03_adaptive_learning, k04_missions, k05_knowledge_continuity, k06_virtual_lab, k07_professional_library, k08_work_assistant, k09_class_overview, k10_organization_center, k11_operations_center, k12_analytics_center, k13_parent_center, k14_communication_center, k15_collaboration_projects, k16_intelligent_core
- Prazdne subory: 297 (ocakavany stav kostry)
- Neprazdne subory pred zmenami: `scripts/build_tree.sh`, `scripts/check_phase.sh`, 6x `*.cpython-314.pyc`, `docs/OPENCODE_PROMPT.md`
- `__pycache__`: 6 adresarov, 6 suborov (zostatky pred git baseline)

## 3. Problemy, odchylky a prekrývania (krok 0.3)

- git: repozitar nebol inicializovany (opravené v 0.4).
- `.gitignore`: bol prazdny (opravené v 0.4).
- sqlite3 CLI nefunkcne (Exec format error); SQLite kniznica v Pythone pouzitelna.
- Nadbytocna polozka `__pycache__` v `backend/app/modules` (nie je sucast zoznamu modulov ako modul, ale je pritomna ako adresar).
- Architektonicke prekrývania, ktore musi kod dodrzat (sekcia 4 promptu): `core/audit` (zapis) vs `k16 audit_engine` (citanie); `core/permissions` vs `k16 rule_system`; `core/events` vs `events/handlers` v moduloch. V tejto faze ide o prazdnu kostru, bez duplicitnej implementacie.

## 4. Zavislosti a overenie (krok 0.5)

- Virtuálne prostredie: `backend/.venv` (Python 3.14.8) vytvorene.
- Instalacia: baliky pre backend nainstalovane mimo tejto relacie (skript `scripts/install_deps.sh` spusteny na pozadi). V relacii sa vykonavali len diagnosticke a overovacie kroky.
- Nezavisle overenie (nahlasene): `cryptography` sa na tomto Androide neda nacitat (`dlopen: cannot locate symbol PyBaseObject_Type`), preto boli odinstalovane `cryptography`, `python-jose`, `rsa`, `ecdsa` a `pyasn1`.
- `backend/requirements.txt`: zmrazeny podla `pip freeze` (presne verzie nizsie).
- Overenie importov v `backend/.venv`: `fastapi, sqlalchemy, alembic, pydantic, pytest, httpx, jwt, argon2` - OK.
- Overenie funkcnosti: vydanie a overenie HS256 tokenu cez `PyJWT` - OK; `argon2-cffi` hash a verify - OK.
- Zakazane kniznice v zavislostiach: `cryptography`, `python-jose`, `passlib`, `rsa`, `ecdsa`, `pyasn1` nie su pritomne (v sulade s D5).

### Presne verzie zavislosti (pip freeze, backend/.venv)

alembic==1.20.1
annotated-doc==0.0.6
annotated-types==0.8.0
anyio==4.16.0
argon2-cffi==25.1.0
argon2-cffi-bindings==26.2.0
certifi==2026.10.23
cffi==2.1.1
click==8.5.1
fastapi==0.163.1
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
Mako==1.4.3
MarkupSafe==3.0.4
opentelemetry-api==1.45.2
packaging==26.3
pluggy==1.7.0
pycparser==3.12
pydantic==2.14.3
pydantic-settings==2.16.3
pydantic_core==2.50.4
Pygments==2.21.0
PyJWT==2.15.1
pytest==9.2.0
python-dotenv==1.2.4
six==1.17.0
SQLAlchemy==2.1.8
starlette==1.10.0
typing-inspection==0.4.5
typing_extensions==4.16.0
uvicorn==0.54.0

## 5. Architektonicke rozhodnutia (ADR)

- D1 (ADR 0002): SQLAlchemy 2.x synchronny, PostgreSQL ciel, SQLite cez DATABASE_URL; bez DB-specifickych funkcii mimo adaptera.
- D2 (ADR 0003): Alembic (`db/migrations`), `db/schema/*.sql` generovane (export do PostgreSQL).
- D3 (ADR 0004): prefixy tabuliek podla 10 datovych oblasti, kazda tabulka prave jedna oblast, test konvencie.
- D4 (ADR 0005): Redis/pgvector za rozhraniami, predvolene in-memory fronta a keyword KnowledgeIndex.
- D5 (ADR 0006, spresnene): PyJWT iba HS256, hesla cez `argon2-cffi`; `cryptography`, `python-jose`, `passlib`, `rsa`, `ecdsa`, `pyasn1` sa nesmu instalovat ani pridavat do requirements.txt.
- D6 (ADR 0007): FileStorage rozhranie, lokalna implementacia mimo gitu.
- D7 (ADR 0008): preklady zdroj v korenovom `locales/`, sync do generovaneho `frontend/src/locales/`.

## 6. Otvorene docasne nastavenia (nie rozhodnutia)

- GRADE_MIN/GRADE_MAX: technicka predvolena hodnota 1 a 9 (docasna, kym pouzivatel nerozhodne).
- AI architektura, zariadenia, nasadenie: podla sekcie 4 promptu (nerozhodnute, implementovat iba rozhrania/konfiguraciu).

## 7. Dalsi krok

Caka sa na schvalenie pouzivatela na zacatie Fazy 1 (jadro: core a shared).
