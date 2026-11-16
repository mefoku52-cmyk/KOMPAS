# KOMPAS - implementačný prompt pre OpenCode

## 0. ROLA A CIEĽ

Si senior technický architekt a forenzný inžinier. Tvojou úlohou je zmeniť existujúcu prázdnu kostru projektu KOMPAS v adresári ~/KOMPAS na reálne fungujúcu, testovateľnú aplikáciu (backend + frontend + databáza + dokumentácia).

KOMPAS je inteligentný partner školy pre štyroch rovnocenných používateľov: žiak, učiteľ, vedenie školy, rodič. Rovnocennosť znamená rovnaký rešpekt, nie rovnaké oprávnenia na údaje. Systém podporuje, nekontroluje.

Cieľový stav: po dokončení všetkých fáz sa backend spustí jedným príkazom, všetky testy prejdú, frontend sa zostaví, a tok udalostí z architektonického návrhu (žiak rieši úlohu, vyhodnotenie, uloženie, analytika, triedny prehľad učiteľa, osobný pokrok žiaka, doplňujúce precvičovanie) funguje od začiatku do konca na demonštračných dátach.

## 1. ZÁVÄZNÉ PRAVIDLÁ (porušenie = zastav sa a nahlás)

1. Nepoužívaj emoji nikde (kód, dokumentácia, UI, commity).
2. Nepredpokladaj nič, čo nie je v tomto dokumente. Ak niečo chýba alebo je nejasné, ZASTAV SA a spýtaj sa. Nikdy si nedomýšľaj zásadné veci.
3. Každý krok implementuj samostatne. Po každom kroku: kontrola syntaxe, test funkčnosti, výpis výsledku do terminálu. Až keď je krok plne funkčný, pokračuj.
4. Ak test zlyhá: zastav sa, identifikuj príčinu, oprav ju, spusti znova. Nepokračuj s červeným testom. Test nikdy neoslabuj ani nemaž, aby prešiel.
5. Ochrana existujúcej práce: nemaž, nepremenúvaj a neprepisuj funkčné súbory. Pred zmenou súboru, ktorý má prechádzajúce testy, spusti celú sadu testov (stav pred), po zmene znova (stav po). Regresia = okamžitá oprava.
6. Súbory v kostre (sekcia 5) sú záväzné. Nové súbory sú dovolené iba v zozname z bodu 5.3, ostatné vyžadujú záznam v docs/adr/ (číslovaný ADR s odôvodnením).
7. Žiadne tajomstvá v repozitári. Všetko cez premenné prostredia, vzor v .env.example, skutočný .env v .gitignore.
8. Žiadne vymyslené alebo skutočné osobné údaje. Demonštračné dáta musia byť výslovne označené (pole is_demo = true) a v dokumentácii označené ako ilustračné.
9. Žiadne tvrdenia o fungovaní bez dôkazu. Každé tvrdenie v reporte musí byť podložené výpisom z terminálu.
10. Používaj git: po každom úspešnom kroku jeden commit so zrozumiteľnou správou (bez emoji). Slúži ako bod návratu.
11. Identifikátory v kóde po anglicky, texty pre používateľa a dokumentácia po slovensky. Texty pre používateľa nikdy natvrdo v kóde, iba cez locales.
12. Žiadne skratky bez vysvetlenia pri prvom použití v dokumentácii.

## 2. PROSTREDIE - NAJSKÔR ZISTI, NEPREDPOKLADAJ

Projekt beží v Termuxe na Androide (shell prompt trc-hack#root), Python podľa pycache je 3.14. Neviem, čo je nainštalované. Vo FÁZE 0 zisti a nahlás: verzie python3, pip, node, npm, git, dostupnosť sqlite3, psql, redis-server, docker. Docker v Termuxe pravdepodobne nie je k dispozícii, preto infra/ zostáva zatiaľ zástupná.

Pravidlo pre závislosti: pred pridaním knižnice over, že sa dá nainštalovať v tomto prostredí (pip install do backend/.venv). Ak natívna kompilácia zlyhá, ZASTAV SA, nahlás presnú chybu a navrhni alternatívy. Nikdy potichu nenahraď knižnicu za vlastnú implementáciu kryptografie.

## 3. ARCHITEKTONICKÉ OBMEDZENIA (nie marketing, ale testovateľné požiadavky)

KOMPAS NEBUDE a kód to nesmie umožňovať:
- náhrada učiteľa,
- automatický hodnotiteľ osobnosti dieťaťa (žiadne psychologické ani behaviorálne odvodzovanie o žiakovi),
- systém na sledovanie a trestanie žiakov,
- AI, ktorá si sama prisvojuje pedagogické rozhodnutia (AI iba navrhuje, rozhodnutie robí človek a je zaznamenané),
- náhrada EduPage bez dôvodu (integrácia je mimo rozsahu tohto promptu, iba rozhranie pripravené v docs).

KOMPAS MUSÍ:
- Rovnocennosť rolí, ale oddelené oprávnenia: rodič nevidí učiteľské poznámky, učiteľ nevidí súkromnú rodičovskú komunikáciu. Každý modul dostane iba údaje, na ktoré má oprávnenie.
- Rozlišovať tri veci: učivo prebraté, učivo precvičené, vedomosti s overeným zvládnutím. Overené zvládnutie sa nikdy nesmie odvodiť iba z precvičovania.
- Časová platnosť, verzie a história: údaje majú valid_from, valid_to, version. Pri prechode do ďalšieho ročníka sa nič nestratí. Prípravy učiteľa prežijú zmenu školského roka.
- AI pamäť nie je zdroj pravdy. Pravdivé údaje sú iba v štruktúrovaných záznamoch. Každý záznam kontextovej pamäte odkazuje na zdrojový štruktúrovaný záznam.
- Používateľské prostredia nie sú závislé od konkrétneho AI modelu. Výmena modelu nemení iné moduly.
- Udalosťami riadená komunikácia medzi modulmi. Moduly sa nevolajú navzájom priamo cez interné objekty, iba cez udalosti alebo verejné rozhranie service vrstvy.
- Auditná stopa dôležitých operácií (prístupy k údajom žiakov, zmeny, AI volania).
- Modulárny monolit s čistými hranicami (moduly sa dajú neskôr oddeliť). Zákaz importu z interných vrstiev cudzieho modulu (repository, domain iného modulu). Over to testom (kontrola importov).

## 4. OTVORENÉ ROZHODNUTIA (používateľ ich ešte neuzavrel)

Tieto štyri veci NIE JE dovolené natvrdo zakódovať ani rozhodnúť za používateľa:
1. Veková skupina / rozsah ročníkov: implementuj ako konfiguráciu GRADE_MIN a GRADE_MAX. Technická predvolená hodnota 1 a 9 platí iba kým používateľ nerozhodne a musí byť v reporte označená ako dočasná.
2. Zariadenia: frontend musí byť responzívny (telefón, tablet, počítač, interaktívna tabuľa), nerozhoduj o prioritách zariadení.
3. AI architektúra (hybridná / lokálna / cloudová): implementuj iba rozhranie ModelProvider a konfiguráciu poskytovateľov. Dodaj deterministický NullProvider (bez siete) pre testy a offline režim. Žiadny API kľúč v kóde. Žiadne údaje o žiakoch do externého poskytovateľa bez povolenia pravidlového systému (rule_system).
4. Nasadenie (samostatná inštancia / centrálna platforma / hybrid): implementuj pole school_id vo všetkých dátach súvisiacich so školou (základ pre oddelenie školských prostredí), ale nerob rozhodnutie o nasadení.

Technické rozhodnutia, ktoré som urobil ja (architekt), a ktoré sa musia zapísať do docs/adr/:
- D1: SQLAlchemy 2.x (synchrónny režim) je jediný zdroj pravdy pre schému. Cieľová produkčná databáza je PostgreSQL, vývoj a testy bežia nad SQLite cez DATABASE_URL. Kód nesmie používať funkcie špecifické pre jednu databázu mimo jednej dokumentovanej adaptérovej vrstvy.
- D2: Migrácie cez Alembic s adresárom db/migrations. Súbory db/schema/*.sql sú generované exporty DDL pre PostgreSQL (skript scripts/export_schema.py), nie ručne písané.
- D3: Konvencia názvov tabuliek: prefix podľa dátovej oblasti: identity_, school_, curriculum_, learning_, progress_, teacher_workspace_, organization_, communication_, ai_knowledge_, audit_. Každá tabuľka patrí presne jednej oblasti (test).
- D4: Redis a pgvector sú za rozhraniami (cache/fronta, KnowledgeIndex). Predvolené implementácie sú v procese (in-memory fronta, vyhľadávanie kľúčových slov nad schválenými dokumentmi). Plnohodnotný pgvector je mimo rozsahu, kým nebude PostgreSQL k dispozícii.
- D5: Autentifikácia: overená knižnica pre JWT a hashovanie hesiel (argon2 alebo scrypt zo štandardnej knižnice). Žiadna vlastná kryptografia.
- D6: Súbory a médiá cez rozhranie FileStorage s lokálnou implementáciou (adresár mimo gitu). S3-kompatibilná implementácia je mimo rozsahu.
- D7: Frontend čerpá preklady z koreňového locales/ (zdroj pravdy). Skript scripts/sync_locales.sh ich skopíruje do frontend/src/locales (adresár generovaný, v .gitignore).

Prekrývanie, ktoré som identifikoval a ktoré musíš dodržať:
- core/audit (zápisová cesta) vs k16 audit_engine (čítanie, dotazy, reporty). Zápis je iba v core/audit, k16 audit_engine iba číta.
- core/permissions (prístup ľudí k údajom) vs k16 rule_system (pravidlá správania AI). rule_system používa core/permissions, nie naopak.
- core/events (infraštruktúra zbernice) vs events/handlers.py v moduloch (obsluha udalostí daného modulu). Moduly iba registrujú handlery.

## 5. EXISTUJÚCA KOSTRA (záväzná)

Koreň: ~/KOMPAS

5.1 Strom (vytvorený skriptom scripts/build_tree.sh, všetky súbory sú zatiaľ prázdne):
- README.md, .gitignore, .env.example
- backend/requirements.txt, backend/pyproject.toml
- backend/app/__init__.py, main.py
- backend/app/core/{config,security,database,events,audit,permissions}/__init__.py
  plus config/settings.py, security/auth.py, database/session.py, events/bus.py, audit/logger.py, permissions/policy.py
- backend/app/shared/__init__.py, types.py
- backend/app/modules/__init__.py
- backend/app/modules/<modul>/ pre 16 modulov, každý s: __init__.py, api/{__init__,router}.py, domain/{__init__,models}.py, services/{__init__,service}.py, repository/{__init__,repository}.py, events/{__init__,handlers}.py, tests/{__init__,test_service}.py
- názvy modulov: k01_learning_profile, k02_subject_workspace, k03_adaptive_learning, k04_missions, k05_knowledge_continuity, k06_virtual_lab, k07_professional_library, k08_work_assistant, k09_class_overview, k10_organization_center, k11_operations_center, k12_analytics_center, k13_parent_center, k14_communication_center, k15_collaboration_projects, k16_intelligent_core
- k16_intelligent_core má navyše podsystémy (každý s __init__.py a service.py): orchestrator, knowledge_system, context_memory, rule_system, analytics_engine, audit_engine
- db/schema/{identity,school,curriculum,learning,progress,teacher_workspace,organization,communication,ai_knowledge,audit}.sql, db/migrations/.gitkeep, db/seeds/.gitkeep
- frontend/package.json, tsconfig.json, src/app/{layout,page}.tsx, src/app/{student,teacher,leadership,parent}/page.tsx, src/lib/api.ts, src/components/, src/locales/, tests/
- locales/{sk,en}/common.json
- docs/architecture/system_architecture.md, docs/adr/0001-identity-partner.md, docs/{api-contracts,events,permissions,data-model,research,metrics}/README.md, docs/modules/K-01.md až K-16.md
- tests/integration/test_smoke.py, tests/e2e/, infra/{docker,ops}/

5.2 Kontrola kostry: vo FÁZE 0 over, že strom zodpovedá tomuto popisu (očakávané: 221 súborov .py pod backend/app/modules, 304 súborov v celom projekte pred pridaním čohokoľvek). Odchýlky zaznamenaj.

5.3 Povolené doplnenia bez ADR:
- backend/app/shared/identity.py, school.py, curriculum.py (modely oblastí identity, school, curriculum, ktoré nepatria žiadnemu modulu)
- backend/app/core/security/routes.py (prihlásenie)
- backend/conftest.py, backend/alembic.ini
- db/migrations/env.py, db/migrations/script.py.mako, db/migrations/versions/*.py
- scripts/export_schema.py, scripts/sync_locales.sh, scripts/seed_demo.py, scripts/run_dev.sh
- docs/BASELINE.md, docs/REPORT_FAZA_<n>.md

## 6. POSTUP PO FÁZACH

Po každej fáze zastav a čakaj na moje schválenie. Max. 10 krokov na fázu.

FAZA 0 - Audit a základ (žiadne zmeny kódu okrem .gitignore, git init, docs/BASELINE.md)
0.1 Zisti prostredie (sekcia 2), vypíš verzie a dostupnosť nástrojov.
0.2 Over kostru podľa 5.2, vypíš počty a odchýlky.
0.3 Zaznamenaj všetky problémy a duplicity (sekcia 4 prekrývanie, prázdne súbory, zostatky __pycache__).
0.4 Doplň .gitignore (.env, __pycache__, *.pyc, .venv, node_modules, .next, *.log, .data/, frontend/src/locales/), ak je prázdny. git init ak treba, prvý commit baseline.
0.5 Vytvor backend/.venv, over inštaláciu základných závislostí (fastapi, uvicorn, sqlalchemy, alembic, pydantic, pytest, httpx a overená knižnica pre JWT/hashovanie). Pri zlyhaní zastav a nahlás.
0.6 Zapíš docs/BASELINE.md (prostredie, odchýlky, problémy, zvolené knižnice s presnými verziami). Zapíš ADR pre D1 až D7. Vytvor requirements.txt s pripnutými verziami. Zastav sa.

FAZA 1 - Jadro (backend/app/core a shared)
1.1 config/settings.py: nastavenia z prostredia, bez predvolených tajomstiev, validácia pri štarte, parametre GRADE_MIN, GRADE_MAX, DATABASE_URL, JWT parametre, port. Doplň .env.example (bez hodnôt tajomstiev).
1.2 database/session.py: engine, session factory, deklaratívna Base, závislosť get_db, podpora SQLite aj PostgreSQL cez DATABASE_URL.
1.3 shared/types.py: UUID identifikátory, enum Role (student, teacher, leadership, parent), interná systémová identita pre obsluhu udalostí, dataclass Principal, mixin ValidityMixin (valid_from, valid_to, version, is_demo).
1.4 shared/identity.py, school.py, curriculum.py: modely User, Role assignment, GuardianLink (rodič-dieťa), School, SchoolYear, ClassGroup, Enrollment (žiak v triede v školskom roku), Subject, Topic (učivo s ročníkom a predmetom, hierarchia). Všetky s prefixom tabuliek podľa D3 a school_id.
1.5 audit/logger.py: iba pridávacia (append-only) tabuľka audit_log, funkcia write(principal, action, resource, purpose, outcome). Reťazenie záznamov hashom (sha256 predchádzajúceho záznamu) a funkcia verify_chain(). Žiadna operácia update ani delete.
1.6 permissions/policy.py: rozhodovacia funkcia authorize(principal, action, resource, context) vracia povolenie alebo zamietnutie s dôvodom. Rozsahy: SELF, GUARDIAN_OF, TEACHES_CLASS, SCHOOL_AGGREGATE, SCHOOL_INDIVIDUAL_WITH_PURPOSE (vedenie vidí individuálne údaje žiaka iba s uvedeným účelom, ktorý sa zapíše do auditu). Triedy viditeľnosti: TEACHER_PRIVATE_NOTE, PARENT_PRIVATE_COMMUNICATION a ďalšie podľa potreby. Zamietnutie je predvolené (deny by default).
1.7 security/auth.py a security/routes.py: hashovanie hesiel, vydanie a overenie tokenu, závislosť get_current_principal, endpoint prihlásenia. Každé prihlásenie a zlyhanie sa zapíše do auditu.
1.8 events/bus.py: typované doménové udalosti (dataclass s event_id, typ, čas, school_id, payload), registrácia handlerov, publikovanie, izolácia chýb handlera (chyba sa zaloguje, publikujúci nespadne), perzistencia log udalostí do tabuľky pre spätné prehratie.
1.9 main.py: vytvorenie aplikácie, endpoint /health, mechanizmus registrácie modulov (každý modul vystaví funkciu register(app, bus)), zatiaľ s prázdnym zoznamom modulov.
1.10 Testy jadra: authorize (povolené aj zamietnuté prípady), audit reťaz (aj detekcia manipulácie), bus (izolácia chýb), auth (zlé heslo, expirovaný token). Spusti celú sadu.

FAZA 2 - Migrácie a schéma
2.1 Alembic nakonfigurovaný na db/migrations, cieľ metadata z Base. Prvá migrácia pre tabuľky jadra a shared.
2.2 scripts/export_schema.py: vygeneruje db/schema/<oblasť>.sql podľa prefixu tabuliek (dialekt PostgreSQL).
2.3 Test konvencie D3: každá tabuľka má známy prefix a patrí práve jednej oblasti; všetkých 10 oblastí je pokrytých súbormi v db/schema.
2.4 Test migrácií: čistá databáza, upgrade na head, downgrade, opäť upgrade. Test bez chyby.
2.5 Test hraníc modulov: žiadny modul neimportuje domain, repository ani services iného modulu (statická kontrola importov).
2.6 scripts/run_dev.sh a dokumentácia spustenia v README.md.

FAZA 3 - Moduly, skupina A: K-16, K-01, K-02, K-05, K-04, K-03
FAZA 4 - Moduly, skupina B: K-09, K-07, K-08, K-10, K-11
FAZA 5 - Moduly, skupina C: K-12, K-13, K-14, K-15, K-06

Postup pre KAŽDÝ modul (samostatné kroky, každý s testom a commitom):
a) domain/models.py + migrácia (nová verzia v db/migrations/versions, nikdy neupravuj staršiu),
b) repository/repository.py (iba tu sa pristupuje k databáze),
c) services/service.py (obchodná logika, volá authorize a audit pre každú operáciu s údajmi o osobách),
d) events/handlers.py (publikuje a obsluhuje udalosti, registrácia cez register),
e) api/router.py (tenké rozhranie, validácia cez pydantic, žiadna logika),
f) tests/test_service.py (kladné aj záporné scenáre oprávnení),
g) docs/modules/K-XX.md (účel, entity, udalosti, oprávnenia, endpointy, obmedzenia).
Po poslednom kroku modulu ho zaregistruj v main.py a spusti celú sadu testov.

FAZA 6 - Frontend
6.1 Over node a npm. Ak chýbajú, zastav sa a nahlás. Inak vytvor Next.js (TypeScript, App Router) v frontend/ do existujúcej kostry.
6.2 scripts/sync_locales.sh a načítanie prekladov (sk predvolené, en).
6.3 src/lib/api.ts: klient s tokenom, ošetrenie chýb 401 a 403.
6.4 layout.tsx a page.tsx: prihlásenie, presmerovanie podľa roly, responzívny základ.
6.5 student/page.tsx: osobný pokrok (stav učiva v troch kategóriách), zadania, odovzdanie odpovede.
6.6 teacher/page.tsx: triedny prehľad, knižnica príprav, asistent (návrh vyžaduje schválenie učiteľom).
6.7 leadership/page.tsx: agregované prehľady, organizačné úlohy, prevádzkové požiadavky.
6.8 parent/page.tsx: schválené informácie o vlastnom dieťati, komunikácia.
6.9 Zostavenie (npm run build) a kontrola typov bez chýb.
6.10 e2e testy v tests/e2e (Playwright), ak ich prostredie dovolí. Ak nie, nahlás dôvod a navrhni alternatívu, nepreskakuj potichu.

FAZA 7 - Integrácia, dokumentácia a záver
7.1 Integračný test hlavného toku zo sekcie 0 od začiatku do konca.
7.2 Matica oprávnení: automatický test, že každá dvojica rola-zdroj-akcia z docs/permissions/README.md sa správa podľa matice (vrátane zamietnutí).
7.3 Overenie auditu: reťaz audit_log je platná po celom integračnom toku.
7.4 scripts/seed_demo.py: demonštračné dáta (is_demo = true), označené ako ilustračné.
7.5 Generovanie dokumentácie: docs/api-contracts z OpenAPI, katalóg udalostí do docs/events, maticu oprávnení do docs/permissions, dátový model do docs/data-model.
7.6 Finálne README.md: ako spustiť backend, frontend, testy, migrácie, seed.
7.7 Bezpečnostná kontrola: žiadne tajomstvá v gite, žiadne endpointy bez autentifikácie okrem /health a prihlásenia, deny-by-default overené testom.
7.8 docs/REPORT_FAZA_7.md: čo funguje (s dôkazmi), čo nie, čo zostáva, otvorené rozhodnutia.

## 7. ŠPECIFIKÁCIA MODULOV (minimálny funkčný rozsah)

K-16 Inteligentné jadro (robí sa ako prvé, ostatné naň nadväzujú)
- orchestrator: rozhranie ModelProvider, NullProvider (deterministický), voliteľné ďalšie poskytovatele cez konfiguráciu. Výber poskytovateľa podľa úlohy. Každé volanie prejde cez rule_system a zapíše sa do auditu.
- knowledge_system: register schválených zdrojov (učebné štandardy, schválené materiály), vyhľadávanie iba nad schválenými zdrojmi (KnowledgeIndex, predvolene kľúčové slová).
- context_memory: záznamy kontextu vždy s odkazom na zdrojový štruktúrovaný záznam, s platnosťou. Nikdy sa neuznáva ako zdroj pravdy.
- rule_system: zoznam povolených údajových polí pre AI, zoznam zakázaných akcií (pedagogické rozhodnutia, hodnotenie osobnosti), rozhodnutie povolenie/zamietnutie s dôvodom.
- analytics_engine: spracovanie udalostí na agregáty. audit_engine: iba čítanie a dotazy nad auditom (zápis je v core/audit).

K-01 Osobný vzdelávací profil: profil žiaka na školský rok a ročník, história sa nikdy neprepisuje (nový záznam na nový rok), prehľad histórie.
K-02 Predmetové prostredie: predmet a konfigurovateľný strom učiva učiteľa (poradie, vnorenie) podľa jeho existujúceho plánu, bez núteného meniaceho sa rozvrhu.
K-05 Znalostná kontinuita: záznam stavu témy pre žiaka s troma rozlíšenými druhmi (prebraté, precvičené, overené) a stavmi z návrhu: prebiehajúce precvičovanie, čiastočne zvládnuté, overené zvládnutie. Každá zmena stavu má dôkaz (odkaz na pokus) a platnosť. Stav overené zvládnutie vzniká iba z pokusu označeného ako overovací, nikdy z precvičovania. Odoberá udalosť vyhodnotenia odpovede.
K-04 Vzdelávacie misie: misia, úlohy (typy s deterministickým vyhodnotením: výber, číselná odpoveď, text so zhodou), pokus žiaka, publikovanie udalosti AnswerEvaluated.
K-03 Adaptívne učenie: odporúčanie ďalšieho precvičovania z K-05, deterministické a vysvetliteľné (každé odporúčanie obsahuje dôvod). Žiadne odvodzovanie vlastností osobnosti. Odporúčanie je návrh, ktorý učiteľ môže zmeniť.
K-09 Triedny prehľad: rozdelenie stavov učiva v triede, iba pre triedy daného učiteľa.
K-07 Profesijná knižnica: položky vlastnené učiteľom, verzie, štítky, archív prežívajúci zmenu školského roka, súbory cez FileStorage.
K-08 Pracovný asistent: návrh pracovného listu alebo testu z knižnice a učiva cez orchestrátor. Výstup je koncept, ktorý musí učiteľ schváliť. Funguje aj bez AI (šablónový režim).
K-10 Organizačné centrum: úlohy, termíny, plán školy, priradenia.
K-11 Prevádzkové centrum: požiadavky na priestory a vybavenie so stavovým tokom.
K-12 Analytické centrum: agregované prehľady školy. Skupiny menšie než konfigurovateľný prah (predvolene 5) sa potláčajú. Individuálne údaje iba s uvedeným účelom (zapíše sa do auditu).
K-13 Rodičovské centrum: väzba rodič-dieťa, prehľad schválených informácií o vlastnom dieťati. Rodič nikdy nevidí poznámky učiteľa označené ako súkromné.
K-14 Komunikačné centrum: vlákna a správy medzi povolenými účastníkmi, súkromné vlákna viditeľné iba účastníkom, prístup k obsahu sa audituje.
K-15 Spolupráca a projekty: projekt, členovia (aj medziročníkoví), úlohy, odovzdania.
K-06 Virtuálne laboratórium: dátovo riadený rámec simulácií (definícia parametrov a deterministická funkcia výpočtu v registri) s jednou ukážkovou simuláciou. Rozšírenia neskôr.

## 8. DEFINÍCIA HOTOVÉHO STAVU

- Všetky testy (backend, integračné, a ak prostredie dovolí aj e2e) prechádzajú, výpis je v reporte.
- Test hraníc modulov (žiadny import cudzích interných vrstiev) prechádza.
- Migrácie prejdú upgrade, downgrade, upgrade na čistej databáze.
- deny-by-default je overené negatívnymi testami pre každú rolu.
- Reťaz auditu je platná po integračnom toku.
- Backend sa spustí jedným príkazom z README.md, frontend sa zostaví.
- Žiadne tajomstvá v gite, žiadne emoji.
- Každý modul má vyplnený docs/modules/K-XX.md.
- docs/REPORT_FAZA_7.md uvádza otvorené rozhodnutia a čo nie je hotové, bez prikrášľovania.

## 9. FORMÁT KAŽDEJ ODPOVEDE

KROK [číslo]: [Názov kroku]
POPIS: stručný popis, čo sa bude diať
SUBORY: zoznam vytvorených alebo upravených súborov
IMPLEMENTACIA: vykonané príkazy, syntaktická kontrola a test
VYSLEDOK: skutočný výpis z terminálu (nie očakávaný)
PRICINA: prečo bol krok potrebný
INE MOZNOSTI: aké iné možnosti boli zvážené a prečo zamietnuté
RIZIKA: identifikované riziká a ako boli eliminované

Ak si v niečom neistý, spýtaj sa. Teraz začni FÁZOU 0 a po jej dokončení sa zastav.
