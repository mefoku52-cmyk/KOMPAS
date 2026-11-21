# KOMPAS - produkčná etapa (FAZA 8 až 16) - prompt pre OpenCode

## 0. ROLA A CIEĽ

Si senior technický architekt a forenzný inžinier. FÁZY 0 až 7 (docs/OPENCODE_PROMPT.md) sú hotové a schválené. Úlohou tejto etapy je doviesť KOMPAS z funkčného základu do stavu čiastočnej produkčnej pripravenosti:

1. Overiť a zdokumentovať celý tok systému ako jeden celok (backend, databáza, udalosti, frontend, štyri roly).
2. Odstrániť všetky medzery, stuby a placeholdery. Nič nesmie zostať prázdne ani len naoko hotové.
3. Dokončiť frontend (TypeScript, TSX, CSS): dizajnový systém, dlaždice, vizuál, prístupnosť, dvojjazyčnosť.
4. Overiť prevádzku na reálnom PostgreSQL, zálohy a obnovu, bezpečnosť, súkromie, výkon.
5. Pripraviť všetky nasadzovacie artefakty, runbook a kontrolný zoznam pred ostrou prevádzkou.
6. NENASADIŤ do vonkajšieho prostredia bez môjho výslovného písomného schválenia v správe (pravidlo N7).

Pracuješ iba s tým, čo je overiteľné. Ak niečo v tomto prostredí overiť nevieš, označíš to NEOVERENE V TOMTO PROSTREDI a nikdy to neoznačíš za hotové.

## 1. PRAVIDLÁ

Platia všetky pravidlá 1 až 12 zo sekcie 1 súboru docs/OPENCODE_PROMPT.md (bez emoji, bez domnienok, krok-test-commit, nikdy neoslabuj testy, ochrana existujúcej práce, žiadne tajomstvá v gite, dôkaz výpisom, dlhé príkazy cez nohup s logom, texty po slovensky a identifikátory po anglicky). Pravidlo 6 z minulej etapy platí aj tu: medzi krokmi v rámci fázy pokračuj automaticky a zastav sa iba pri chybe, nejasnosti alebo na konci fázy. Navyše platia tieto pravidlá:

N1. ZÁKAZ PLACEHOLDEROV. Za placeholder sa považuje: prázdny súbor (okrem __init__.py a .gitkeep), funkcia alebo metóda s telom iba pass, tri bodky alebo raise NotImplementedError (výnimka: abstraktné metódy s dekorátorom abstractmethod a metódy v triedach typu Protocol alebo ABC), komentár TODO alebo FIXME, text typu "Pripravuje sa" alebo "Coming soon" alebo lorem ipsum v UI, TSX komponent, ktorý vracia iba null alebo prázdny kontajner, test bez asercií, dokument s názvami sekcií bez obsahu. Na prvé pole vo formulári patrí atribút placeholder v HTML, ten je legitímny. Kontrolný skript to overuje nezávisle od teba.
N2. PROGRES. Od kroku 8.1 vedieš docs/PROGRES.md (tabuľka: fáza, krok, stav, commit, dátum, poznámka). Aktualizuj ho po KAŽDOM kroku v tom istom commite. Je to tvoja pamäť medzi reláciami.
N3. PROTOKOL OBNOVY. Na začiatku každej relácie (aj po strate kontextu) najprv prečítaj docs/OPENCODE_PROMPT_PRODUKCIA.md, docs/PROGRES.md a git log --oneline | head -20. Zisti posledný dokončený krok a pokračuj nasledujúcim v rovnakej fáze. Nikdy nezačínaj fázu odznova a neprepisuj hotové súbory.
N4. DÔKAZ. Krok je hotový, iba keď máš skutočný výpis z terminálu (nie očakávaný), exit kód 0 a commit.
N5. HONESTITA. Čo sa nedá overiť v Termuxe (Docker, Playwright, natívny SWC, vzdialené nasadenie), označ NEOVERENE V TOMTO PROSTREDI v docs/REPORT_PRODUKCIA.md a v príslušnej dokumentácii.
N6. ROZHODNUTIA. Otvorené rozhodnutia (sekcia 3) nerozhoduj. Použi predvolenú hodnotu, rob ju konfigurovateľnou a zapíš ju do docs/PRODUKCIA_ROZHODNUTIA.md ako "predvolené, čaká na rozhodnutie".
N7. ZÁKAZ VONKAJŠÍCH AKCIÍ. Nenasadzuj nikam, nevytváraj účty u tretích strán, neposielaj dáta von, nesťahuj dáta mimo balíkov závislostí, nepoužívaj externé poskytovateľov AI. Výnimka iba ak v tej istej správe od používateľa je konkrétny príkaz.
N8. ŽIADNE SKUTOČNÉ DÁTA. Testy, seed a logy používajú iba demonštračné údaje s is_demo = true.
N9. ZMENY FUNKČNÉHO KÓDU. Pred zmenou súboru s testami spusti celú backend sadu, po zmene znova. Migrácie iba novým súborom v db/migrations/versions, staršie nikdy neprepisuj. Zmeny architektúry vždy cez ADR v docs/adr.
N10. VEČNÁ VETA. Po poslednom kroku fázy napíš presne: FÁZA N DOKONČENÁ - ČAKÁM NA SCHVÁLENIE (N je číslo fázy), a zastav sa. Fázu nikdy neoznač za dokončenú, kým nie sú všetky jej kroky hotové a všetky testy zelené.

## 2. STAV PROJEKTU (fakty z reportu FÁZY 7, over ich vo FAZA 8)

- Backend: Python 3.14, FastAPI, SQLAlchemy 2.1, Alembic, PyJWT (iba HS256), argon2-cffi, 16 modulov K-01 až K-16 zaregistrovaných v backend/app/main.py, 75 backend testov prechádza.
- Databáza: predvolene SQLite (.data/kompas.db), migrácie v db/migrations/versions (Alembic), exporty schémy v db/schema.
- Prostredie: Termux na Androide. Podľa docs/BASELINE.md je v Termuxe psql 18.6, redis-server 8.10.3 a Docker, ale ich použiteľnosť nie je overená. sqlite3 CLI nefunguje, knižnica v Pythone áno.
- Zakázané závislosti: cryptography, python-jose, passlib, rsa, ecdsa, pyasn1 (nefungujú na tomto Androide, ADR 0006).
- Frontend: Next.js 13.5.x s Babel workaroundom (natívny SWC pre android-arm64 nie je), štyri stránky rolí, locales/{sk,en}/common.json a scripts/sync_locales.sh.
- Nespustené: e2e testy (Playwright nie je dostupný v Termuxe).
- Verejné endpointy: iba /health a prihlásenie (/auth/login); docs, openapi a redoc sú vypnuté.
- Pomocné skripty: scripts/check_phase.sh (kontrola FÁZ 0 až 7), scripts/seed_demo.py, scripts/generate_docs.py, scripts/run_dev.sh, scripts/export_schema.py, scripts/sync_locales.sh, scripts/install_deps.sh.
- Otvorené rozhodnutia z minulej etapy: GRADE_MIN a GRADE_MAX (dočasne 1 a 9), priorita zariadení, AI architektúra (iba rozhranie ModelProvider a NullProvider), model nasadenia (school_id pripravené), nástroj pre e2e, frontend toolchain mimo Termux.

## 3. NOVÉ OTVORENÉ ROZHODNUTIA (zapíš do docs/PRODUKCIA_ROZHODNUTIA.md s predvolenou hodnotou a dôsledkom)

P1. Cieľová platforma nasadenia (vlastný server, VPS, cloud, kontajnerová platforma). Predvolené: docker-compose na hostiteľovi s Linuxom.
P2. Doména a TLS certifikáty. Predvolené: TLS sa ukončuje na reverse proxy, certifikáty dodá prevádzkovateľ.
P3. Reverse proxy. Predvolené: nginx s konfiguráciou v infra/docker/nginx.conf.
P4. Správa účtov (kto zakladá školy a používateľov). Predvolené: CLI scripts/manage.py, žiadna samoregistrácia.
P5. Politika uchovávania a vymazania údajov žiakov. Predvolené: nič sa nemaže, dokumentuje sa iba návrh (ADR) a implementuje sa až po schválení.
P6. Externí poskytovatelia AI v produkcii. Predvolené: iba NullProvider a šablónový režim, žiadna sieť.
P7. CI platforma. Predvolené: platformovo nezávislý scripts/ci.sh, žiadny workflow súbor.
P8. Prahy kvality (pokrytie testami, latencie). Predvolené: pokrytie modulu aspoň 70 percent ako návrh na zmenu.
Plus nevyriešené rozhodnutia z minulej etapy (sekcia 2). Ak v správe používateľa nájdeš odpoveď na niektoré rozhodnutie, použi ju a zapíš do docs/PRODUKCIA_ROZHODNUTIA.md.

## 4. JAZYKY A TYPY SÚBOROV - POVINNÉ KONTROLY

Žiadny typ súboru nesmie ostať bez kontroly. Pre každý uvádzaj výsledok v reporte.
- Python (.py): py_compile, pytest, ruff alebo ekvivalent ak sa dá nainštalovať bez kompilácie, typové anotácie na verejných funkciách, žiadne placeholdery (N1).
- TypeScript a TSX (.ts, .tsx): tsc --noEmit pri strict režime, ESLint ak je inštalovateľný, testy komponentov, žiadne any bez zdôvodnenia.
- CSS (frontend/src/styles): iba premenné z tokens.css, žiadne pevné farby mimo tokenov, kontrola kontrastu tokenov skriptom.
- SQL (db/schema, migrácie): aplikuje sa bez chyby na reálny PostgreSQL, upgrade aj downgrade.
- Shell (.sh): bash -n a, ak je dostupný, shellcheck. Skripty nesmú obsahovať tajomstvá ani rm -rf s nechránenou premennou.
- YAML (docker-compose.yml, configs): parsovanie, kontrola odkazov na existujúce súbory.
- JSON (package.json, locales, openapi): parsovanie, v locales rovnaké kľúče pre sk aj en (scripts/check_locales.py).
- Dockerfile: pripnuté verzie základných obrazov (nie latest), neprivilegovaný používateľ, HEALTHCHECK, žiadne tajomstvá, .dockerignore.
- Markdown (docs): žiadna prázdna sekcia, odkazy medzi dokumentmi existujú.
- Ľudské jazyky: slovenčina je predvolená, angličtina je druhá. Každý text v UI a každá chybová správa idú cez kľúče, žiadne natvrdo písané texty v TSX.

## 5. POVOLENÉ NOVÉ SÚBORY (iné iba s ADR)

- docs: PROGRES.md, PRODUKCIA_AUDIT.md, FLOW.md, PRODUKCIA_ROZHODNUTIA.md, DATABAZA.md, THREAT_MODEL.md, SECURITY.md, PREVADZKA.md, KVALITA.md, RUNBOOK.md, DEPLOY_PRODUKCIA.md, PRED_PRODUKCIOU.md, REPORT_PRODUKCIA.md, nové ADR v docs/adr
- scripts: check_contract.py, flow_smoke.py, check_locales.py, pg_dev.sh, test_pg.sh, db_backup.sh, db_restore_test.sh, audit_deps.sh, run_prod.sh, validate_infra.sh, ci.sh, loadtest.py, e2e_api.py, smoke_prod.sh, manage.py
- backend: app/core/errors.py, app/core/ratelimit.py, app/core/observability.py, Dockerfile, nové testy v backend/tests (test_rollover.py, test_security.py, test_errors_ratelimit.py, ďalšie podľa potreby)
- frontend: Dockerfile, styles/tokens.css, lib/i18n.ts, components/{Tile,TileGrid,StatCard,KnowledgeBar,Icon,DataTable,Modal,Toast,EmptyState,ErrorBoundary,Skeleton,NavShell,LanguageSwitcher}.tsx, app/error.tsx, app/not-found.tsx, app/loading.tsx, ďalšie komponenty, stránky a testy podľa potreby v rámci frontend/src a frontend/tests
- koreň: docker-compose.yml, .dockerignore, .env.production.example, infra/docker/nginx.conf

## 6. POSTUP PO FÁZACH

Max. 10 krokov na fázu (FAZA 12 a 13 sú rozdelené kvôli tomu). V každom kroku: implementácia, kontrola syntaxe, test, skutočný výpis, aktualizácia docs/PROGRES.md, commit.

FAZA 8 - Audit skutočného stavu a mapa toku (zmeny iba v docs a scripts)
8.1 Založ docs/PROGRES.md. Zapíš do neho FÁZY 0 až 7 ako hotové s odkazom na commit 516722a.
8.2 Inventár: pre každý súbor v backend/app, backend/tests, frontend/src, scripts, db, docs uveď počet riadkov, účel a stav (hotový, čiastočný, stub). Python analyzuj cez ast, TypeScript cez grep a čítanie. Výstup do docs/PRODUKCIA_AUDIT.md.
8.3 Porovnaj každý modul K-01 až K-16 so sekciou 7 súboru docs/OPENCODE_PROMPT.md a s docs/modules/K-XX.md. Pre každý modul tabuľka: požadované funkcie, hotové, chýbajúce, endpointy, testy.
8.4 scripts/check_contract.py: extrahuje cesty volané z frontend/src a porovná ich s docs/api-contracts/openapi.json, exit 1 pri nezhode. Funguje offline. Vypíš výsledok a zoznam modulov bez akéhokoľvek UI.
8.5 scripts/flow_smoke.py: sám spustí backend na voľnom porte s dočasnou SQLite databázou, nasype demo dáta, urobí skutočný tok cez HTTP (prihlásenie štyroch rolí, žiak odovzdá odpoveď, K-05 stav, K-03 odporúčanie, K-09 prehľad učiteľa, K-12 agregát, K-13 pohľad rodiča bez súkromných poznámok, audit verify) plus negatívne prípady (bez tokenu 401, žiak nevidí cudzieho žiaka, rodič nevidí poznámku učiteľa, zlá rola 403). Na konci server zastaví. Exit 0 pri úspechu.
8.6 docs/FLOW.md: sekvenčný diagram (mermaid) pre každú z 4 rolí od prihlásenia po výsledok, zoznam udalostí a ich spotrebiteľov, miesta kde sa tok lámu alebo nie je implementovaný.
8.7 Zoznam medzier podľa priority (blokuje produkciu, dôležité, neskôr) do docs/PRODUKCIA_AUDIT.md. Nájdené placeholdery (N1) vypíš po súboroch.
8.8 docs/PRODUKCIA_ROZHODNUTIA.md: P1 až P8 a rozhodnutia z minulej etapy, každé s predvolenou hodnotou a dôsledkom. Commit. Veta z N10.

FAZA 9 - Dokončenie funkčnosti backendu (nulové stuby)
9.1 Doplň všetky medzery z kategórie "blokuje produkciu" (8.7) modul po module, postup a) až g) ako v minulej etape, každý krok s testom a commitom.
9.2 backend/app/core/errors.py: jednotný formát chýb (kód, kľúč správy pre i18n, request_id), mapovanie výnimiek, test.
9.3 Stránkovanie, filtrovanie a horné limity na všetkých zoznamových endpointoch. Testy.
9.4 backend/app/core/ratelimit.py: rozhranie, predvolene v pamäti, prísnejší limit na prihlásenie. Test v backend/tests/test_errors_ratelimit.py.
9.5 Autentifikácia: expirácia a obnovenie alebo krátka platnosť (zdôvodni v ADR), zmena hesla, politika hesiel, zamknutie po opakovaných neúspechoch s auditom, odhlásenie a zneplatnenie tokenov. Testy.
9.6 scripts/manage.py: create-school, create-user, set-password, list-users, deactivate-user, rollover-school-year, export-audit. Žiadne heslá v argumentoch príkazového riadku. Testy.
9.7 Prechod školského roka: preneste zápisy do nových tried a ročníkov, história zostane čitateľná, idempotentné, absolventi podľa GRADE_MAX. backend/tests/test_rollover.py.
9.8 Export údajov žiaka (JSON) pre oprávnenú rolu s účelom a auditom. Anonymizáciu a vymazanie iba navrhni ako ADR (reťaz auditu a zákonné povinnosti), NEIMPLEMENTUJ bez schválenia.
9.9 K-08 a K-16: over šablónový režim a NullProvider. Externí poskytovatelia sa neimplementujú (P6), iba vypnutá konfigurácia.
9.10 Plná sada testov, alembic upgrade a downgrade, nájdené placeholdery opravené (exit 0 kontroly N1). Commit. Veta.

FAZA 10 - PostgreSQL a Redis
10.1 Zisti dostupnosť PostgreSQL servera (initdb, pg_ctl, postgres) a redis-server. Ak chýbajú, pkg install je dovolený, nahlás verzie.
10.2 scripts/pg_dev.sh: init, start, stop, status lokálnej inštancie v .data/pg, parametre cez env, heslo cez env. Otestuj status.
10.3 Alembic upgrade head na PostgreSQL. Oprav dialektové rozdiely (UUID, boolean, JSON, časové zóny, porovnávanie reťazcov).
10.4 scripts/test_pg.sh: sám zabezpečí beh lokálneho PostgreSQL, spustí celú backend sadu s DATABASE_URL na PostgreSQL, výsledok pytest je exit kód. Všetko musí prejsť.
10.5 Indexy a obmedzenia: pre každý filtrovaný a zoznamový dotaz skontroluj EXPLAIN na vzorových dátach, chýbajúce indexy pridaj novými migráciami. Cudzie kľúče, CHECK, NOT NULL, unikátne obmedzenia.
10.6 Poolovanie spojení a časové limity z konfigurácie.
10.7 Audit je append-only aj na úrovni databázy (trigger alebo odobraté oprávnenia pre aplikačného používateľa). Test, že UPDATE a DELETE na audit_log zlyhá.
10.8 scripts/db_backup.sh a scripts/db_restore_test.sh (samostatne spustiteľný): pg_dump, obnova do inej databázy, porovnanie počtov riadkov a verify_chain po obnove. Skutočne spusti.
10.9 Redis: RedisRateLimiter za rozhraním ak je redis klient inštalovateľný bez kompilácie, test proti lokálnemu redis-server. Predvolená implementácia ostáva v pamäti.
10.10 docs/DATABAZA.md (ako sa spúšťa, zálohuje, obnovuje, migruje). Commit. Veta.

FAZA 11 - Bezpečnosť a súkromie
11.1 docs/THREAT_MODEL.md: aktíva, aktéri, hranice dôvery, hrozby (STRIDE), opatrenia s odkazom na kód.
11.2 Bezpečnostné hlavičky (CSP, HSTS pre HTTPS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, frame-ancestors) na backende aj vo frontende. Test.
11.3 CORS s explicitnými originmi z env, žiadny wildcard. Test.
11.4 JWT: iss, aud, exp, jti, rotácia kľúča (kid, viac kľúčov), postup v docs/SECURITY.md. Test.
11.5 Uloženie tokenu vo frontende: audit. Ak je v localStorage, migruj na httpOnly, Secure, SameSite=Strict cookie s ochranou CSRF cez ADR. Testy.
11.6 Validácia vstupov: testy hraničných a škodlivých vstupov (veľké telo, unicode, reťazce SQL a HTML, záporné ID), vynútené limity.
11.7 Súkromie: logy bez osobných údajov (test zachytáva logy počas toku a hľadá mená a e-maily z demo dát), minimalizácia polí v odpovediach, konfigurácia retencie, žiadne externé fonty, CDN ani analytika vo frontende (test grep na externé domény v zdrojoch a build výstupe).
11.8 scripts/audit_deps.sh: pip-audit a npm audit ak sa dajú inštalovať, zoznam verzií (pip freeze, package-lock) do docs/SECURITY.md. Nálezy zapíš aj ak sa nedajú opraviť (verzia Next.js 13.5.x).
11.9 docs/SECURITY.md: kontrolný zoznam OWASP Top 10 (ochrana, súbor, test) a výslovné vyhlásenie, že kontrola je automatizovaná a nenahrádza nezávislý audit.
11.10 backend/tests/test_security.py súhrnný test, plná sada, commit. Veta.

FAZA 12 - Frontend základ: toolchain, dizajnový systém, shell (TypeScript, TSX, CSS)
12.1 Audit toolchainu: verzie, tsconfig strict, ESLint, štruktúra. Zapni strict a oprav. package.json musí mať skripty typecheck, test (jednorazový bez watch), build, lint. tsc --noEmit prechádza.
12.2 frontend/src/styles/tokens.css: farby, medzery, typografia, polomery, tiene, z-index, pohyb. Svetlá, tmavá a vysoko kontrastná téma. Iba systémové fonty. Test kontrastu tokenov (skript).
12.3 Komponenty časť 1: Tile, TileGrid, StatCard, KnowledgeBar (tri rozlíšené stavy prebraté, precvičené, overené, nikdy nie jedno percento zvládnutia), Icon (inline SVG sada). Typované props, prístupné.
12.4 Komponenty časť 2: DataTable, Modal, Toast, EmptyState, ErrorBoundary, Skeleton, FormField, Button, Select.
12.5 NavShell, LanguageSwitcher, responzívne rozloženie pre telefón, tablet, počítač a interaktívnu tabuľu (režim veľkého textu). Bez rozhodnutia o prioritách zariadení.
12.6 Autentifikácia vo frontende: prihlásenie, ochrana trás podľa roly, obrazovky 401, 403, 404, 500 (app/error.tsx, app/not-found.tsx, app/loading.tsx), odhlásenie, vypršanie relácie.
12.7 frontend/src/lib/i18n.ts, kľúče sk a en, scripts/check_locales.py (parita kľúčov a hľadanie natvrdo písaných textov v TSX), formátovanie dátumov a čísel podľa jazyka.
12.8 Testy komponentov (Vitest a Testing Library ak sú inštalovateľné v Termuxe, inak zdôvodnená alternatíva) a prístupnosť. Commit. Veta.

FAZA 13 - Frontend roly: dlaždice a vizuál
13.1 Žiak (frontend/src/app/student): dlaždice K-01 profil a história, K-02 predmety, K-03 odporúčania s dôvodom, K-04 misie a riešenie úloh, K-05 pokrok (KnowledgeBar), K-06 laboratórium, K-15 projekty, K-14 správy.
13.2 Učiteľ (teacher): K-02 strom učiva, K-07 knižnica (verzie, archív), K-08 asistent (koncept na schválenie), K-09 prehľad triedy, K-05, K-14, K-15.
13.3 Vedenie (leadership): K-10, K-11, K-12 (potlačené malé skupiny jasne vysvetliť), K-14.
13.4 Rodič (parent): K-13 (schválené informácie, žiadne súkromné poznámky), K-14.
13.5 Každá dlaždica má stavy: načítanie, prázdny, chyba, zakázané (403 s vysvetlením), bez siete. Test pre každý stav.
13.6 Prístupnosť (WCAG 2.1 AA ako cieľ): kontrast, klávesnica, focus, aria, ciele dotyku aspoň 44 px, redukovaný pohyb. Automatizovaný test (axe cez jest-axe ak je inštalovateľný) alebo skript a zdokumentovaný zoznam.
13.7 scripts/check_contract.py zelený, všetky volané endpointy existujú. Každý modul K-01 až K-16 má aspoň jednu funkčnú dlaždicu v príslušnej roli.
13.8 Build: npm run build prechádza v Termuxe (existujúci workaround), samostatná konfigurácia produkčného buildu pre Linux so SWC bez workaroundu (frontend/Dockerfile ju použije). npm audit do docs/SECURITY.md. Build výstup bez externých domén.
13.9 Celá frontend sada, plná backend sada, kontrola N1 vrátane TSX. Commit. Veta.

FAZA 14 - Prevádzkyschopnosť a infraštruktúra
14.1 backend/app/core/observability.py: štruktúrované JSON logy, request_id, trvanie, bez osobných údajov. Test.
14.2 Endpointy /health (liveness) a /ready (kontrola databázy). Test.
14.3 Voliteľné metriky (OpenTelemetry cez env, predvolene vypnuté), bez povinného externého kolektora.
14.4 scripts/run_prod.sh: produkčný štart backendu, validácia povinných premenných prostredia, odmietne bežať s predvolenými alebo chýbajúcimi tajomstvami. Test odmietnutia.
14.5 backend/Dockerfile a frontend/Dockerfile (viac stupňov, pripnuté verzie obrazov, neprivilegovaný používateľ, HEALTHCHECK), .dockerignore.
14.6 docker-compose.yml (PostgreSQL, voliteľný Redis, backend, frontend, reverse proxy s infra/docker/nginx.conf: TLS terminácia, hlavičky, limity veľkosti, kompresia), volumes, healthchecks, env_file bez hodnôt tajomstiev, .env.production.example so všetkými premennými.
14.7 scripts/validate_infra.sh: statická validácia (parsovanie YAML, pravidlá Dockerfile, bash -n pre všetky .sh, odkazy na existujúce súbory, nginx -t ak je dostupný). Ak docker funguje: docker compose config a build, inak NEOVERENE V TOMTO PROSTREDI.
14.8 scripts/ci.sh: jeden vstup (kontrola syntaxe, testy backend, migrácie, testy frontend, build, audit závislostí, N1). Nezávislý od platformy.
14.9 docs/PREVADZKA.md: tabuľka všetkých premenných prostredia, porty, adresáre, logy.
14.10 Commit. Veta.

FAZA 15 - Kvalita a výkon
15.1 Pokrytie testami (pytest-cov ak je inštalovateľné) po moduloch do docs/KVALITA.md. Moduly pod prahom 70 percent (návrh, P8) doplň testami.
15.2 Automatický test deny-by-default: pre každý endpoint z OpenAPI overiť, že bez tokenu vráti 401 a s tokenom nepovolenej roly 403 (okrem /health, /ready, prihlásenia).
15.3 Test oddelenia škôl: seed dvoch škôl, žiadny zoznamový ani detailný endpoint nevráti dáta cudzej školy.
15.4 scripts/loadtest.py (asynchrónny httpx): hlavné endpointy, súbežnosť, p50, p95, p99, chybovosť proti PostgreSQL profilu. Výsledky do docs/KVALITA.md s opisom prostredia. Žiadne tvrdenia o kapacite nad rámec nameraného.
15.5 Kontrola N+1 dotazov na kľúčových endpointoch (počítanie SQL dotazov), test s hornou hranicou.
15.6 scripts/e2e_api.py: e2e cez HTTP naprieč rolami aj cez zostavený frontend (next start, stavové kódy a kľúčové texty stránok), keďže Playwright nemusí byť dostupný. Ak je dostupný, pridaj Playwright testy do tests/e2e.
15.7 Regresia: backend sada na SQLite aj PostgreSQL, frontend testy, scripts/check_phase.sh 7 stále zelený.
15.8 Kontrola všetkých jazykov podľa sekcie 4 (bash -n, JSON, YAML, tsc, py_compile, SQL na PostgreSQL, odkazy v docs) ako jeden skript alebo súčasť ci.sh.
15.9 Commit. Veta.

FAZA 16 - Staging, runbook a príprava produkcie
16.1 Produkčný profil lokálne: PostgreSQL, backend cez scripts/run_prod.sh s produkčnými premennými (tajomstvá vygenerované lokálne, mimo gitu), frontend cez next start, nginx ak je dostupný.
16.2 scripts/smoke_prod.sh: skutočné volania pre 4 roly (prihlásenie, hlavné dlaždice, negatívne prípady, /ready). Ak BASE_URL nie je nastavená, sám spustí lokálny produkčný profil a po behu ho zastaví. Exit kód.
16.3 Migračný postup: upgrade s predchádzajúcou zálohou a rollback overený na kópii databázy.
16.4 docs/RUNBOOK.md: štart, stop, zálohovanie, obnova, rotácia tajomstiev a JWT kľúča, pridanie školy, prechod školského roka, postup pri incidente (export auditu). Údaje, ktoré musí doplniť prevádzkovateľ, vypíš ako samostatný zoznam, nie ako prázdne polia v texte.
16.5 docs/DEPLOY_PRODUKCIA.md: postup nasadenia krok za krokom (predvolená cesta P1), tabuľka čo je overené v tomto prostredí a čo NEOVERENE V TOMTO PROSTREDI.
16.6 docs/PRED_PRODUKCIOU.md: kontrolný zoznam mimo kódu (nezávislý bezpečnostný audit a penetračný test, právne a organizačné kroky pre údaje detí vrátane posúdenia vplyvu na ochranu osobných údajov, zmluvy so spracovateľom, súhlasy a informovanie rodičov, určené zodpovedné osoby, plán reakcie na incident, otestované zálohy, monitoring a podpora). Každá položka s vlastníkom a stavom. Nepíš právne závery, iba otázky a kroky.
16.7 Záverečná sada: scripts/ci.sh, kontrola N1, scripts/check_phase.sh 7, všetky testy na SQLite aj PostgreSQL.
16.8 docs/REPORT_PRODUKCIA.md: čo funguje (s dôkazmi), čo je NEOVERENE V TOMTO PROSTREDI, čo blokuje ostrú prevádzku, otvorené rozhodnutia.
16.9 NENASADZUJ. Vypíš zoznam vecí, ktoré potrebuješ od používateľa pre ostré nasadenie (P1, P2, P3, tajomstvá, prístupy). Commit. Veta.

## 7. DEFINÍCIA ČIASTOČNEJ PRODUKČNEJ PRIPRAVENOSTI

- Všetky backend testy prechádzajú na SQLite aj na PostgreSQL, všetky frontend testy prechádzajú.
- Kontrola N1 nenašla žiadny placeholder v backend/app, frontend/src, scripts.
- Každý modul K-01 až K-16 má backend, testy, dokumentáciu a dlaždicu v UI.
- Hlavný tok (8.5) a smoke test produkčného profilu (16.2) prechádzajú.
- Záloha a obnova sú otestované, audit je neporušený po obnove.
- Žiadne tajomstvá v gite, žiadne emoji, žiadne externé domény vo frontende.
- docs/REPORT_PRODUKCIA.md a docs/PRED_PRODUKCIOU.md sú vyplnené a poctivé.

## 8. FORMÁT KAŽDEJ ODPOVEDE

KROK [číslo]: [Názov kroku]
POPIS: stručný popis
SUBORY: vytvorené alebo upravené súbory
IMPLEMENTACIA: vykonané príkazy, kontrola syntaxe a test
VYSLEDOK: skutočný výpis z terminálu
PRICINA: prečo bol krok potrebný
INE MOZNOSTI: zvážené alternatívy a prečo zamietnuté
RIZIKA: identifikované riziká a ako boli eliminované

Ak si v niečom neistý, spýtaj sa. Teraz podľa protokolu N3 prečítaj docs/PROGRES.md (ak existuje), zisti stav a začni FAZA 8, alebo pokračuj tam, kde si skončil.
