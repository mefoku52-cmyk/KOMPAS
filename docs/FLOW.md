# FLOW - skutočný priebeh systému (FÁZA 8)

Dokument popisuje reálne implementované prepojenie modulov podľa aktuálneho stavu kódu, OpenAPI a smoke/audit z FÁZY 8. Neuvádza cieľový stav, ktorý nie je v kóde.

## Overené skutočné stavy

- **HTTP/API (aktuálne):** verejné sú `/health` a `/auth/login` (docs/openapi/redoc vypnuté). Väčšina modulov vystavuje iba `GET /kNN/status` (K-01,K-02,K-03,K-04,K-05,K-07,K-08,K-09,K-10,K-11,K-16) alebo nemá doménové HTTP cesty v OpenAPI (K-06 prefix `/lab`, K-12 `/analytics`, K-13 `/parent`, K-14 `/communication`, K-15 `/projects` majú prázdne/bez doménových ciest routery). Frontend reálne volá iba `POST /auth/login` (`frontend/src/lib/api.ts`).
- **Tok na úrovni služieb/testov (overené):** integrácia jadra a modulov je overená v `backend/tests/test_integration_main_flow.py` a modulových testoch (spolu 75 passed pri poslednom behu F7). Tam prebieha skutočná doménová logika (odpoveď -> stav zvládnutia -> odporúčanie -> prehľad učiteľa -> agregát -> rodič, audit verify) cez service/DB vrstvy, nie cez verejné HTTP endpointy.

## 1. Žiak sa prihlási
- **Vstup:** používateľské meno/heslo (`POST /auth/login`).
- **Overenie identity:** K-16 / core security (`authenticate_user`, `hash_password`/verify, `create_access_token` s rolami a `school_id`), dáta v `identity_user` + `identity_role_assignment`.
- **Výstup:** JWT `access_token`; frontend ho uloží a presmeruje podľa role (`frontend/src/app/page.tsx`, stránky `student|teacher|leadership|parent`).
- **Stav:** plne funkčné cez HTTP (overené `scripts/flow_smoke.py` pre student/teacher/leadership/parent). Negatívny prípad zlé heslo -> 401.

## 2. Žiak dostane alebo rieši úlohu (K-01, K-04)
- **Implementácia:** K-01 (obsah/curriculum) a K-04 (practice & feedback) majú doménovú logiku v service/repository vrstvách a DB tabuľkách (`curriculum_*`, `learning_content_item`, `learning_practice_*`), testy existujú.
- **HTTP:** iba `/k01/status`, `/k04/status`; doménové endpointy na výber/priradenie/submit úlohy **nie sú vystavené**.
- **Skutočný priebeh:** submit odpovede a vyhodnotenie prebieha na úrovni služieb (integračný test), nie cez HTTP. Gap: žiak nevie cez aktuálne API/UI odoslať odpoveď.

## 3. Vznikne záznam výkonu a aktualizuje sa stav zvládnutia (K-05)
- **Implementácia:** K-05 `StudentStateService`/repo ukladá `learning_mastery_state` (mastery/streak/needs_help a pod.), modulové a integračné testy overujú aktualizáciu po odpovedi.
- **HTTP:** iba `/k05/status`; endpoint na čítanie stavu žiaka **nie je vystavený**.
- **Skutočný priebeh:** aktualizácia stavu nastáva v rámci service toku po spracovaní odpovede (K-04 -> K-05). Gap: stav nie je čitateľný cez HTTP.

## 4. Adaptácia vygeneruje odporúčanie (K-03)
- **Implementácia:** K-03 `AdaptationService` generuje odporúčanie na základe stavu (service/DB), testy existujú.
- **HTTP:** iba `/k03/status`; endpoint odporúčania **nie je vystavený**.
- **Skutočný priebeh:** odporúčanie vzniká v service/integration toku. Gap: nedostupné cez HTTP/UI.

## 5. Učiteľ uvidí žiaka v prehľade triedy (K-09)
- **Implementácia:** K-09 `TeacherInsightService` poskytuje prehľad/insighty nad stavmi žiakov, testy existujú.
- **HTTP:** iba `/k09/status`; endpoint prehľadu **nie je vystavený**.
- **Skutočný priebeh:** prehľad je dostupný cez service vrstvu (testy). UI rola teacher existuje ako stránka bez doménových dátových volaní. Gap: učiteľ nevidí dáta cez HTTP/UI.

## 6. Vedenie uvidí agregát (K-12)
- **Implementácia:** K-12 má snapshoty `progress_analytics_snapshot` a agregačnú logiku v službách, migrácia a testy existujú.
- **HTTP:** prefix `/analytics`, ale doménové cesty v OpenAPI/routeri **chýbajú** (`/analytics/overview` nedostupný).
- **Skutočný priebeh:** agregácia overená na úrovni služieb/testov. UI leadership bez dátových volaní. Gap: agregát nedostupný cez HTTP/UI.

## 7. Rodič uvidí čo má vidieť (K-13)
- **Implementácia:** K-13 nadväzuje na `identity_guardian_link`, filtrovanie viditeľnosti pre rodiča v službách, testy existujú.
- **HTTP:** prefix `/parent`, doménové cesty v OpenAPI **chýbajú**. Frontend stránka `/parent` je UI bez API volania.
- **Skutočný priebeh:** rodičovský pohľad overený v service/integration testoch (vrátane obmedzení). Gap: nedostupné cez HTTP/UI.

## 8. Audit zachytí kritické udalosti
- **Implementácia:** append-only audit (`audit_log`, hash chain), `AuditService.verify_chain()`; overené v integračných/perm testoch F7 (chain `(True, None)`).
- **HTTP:** audit verify **nie je vystavený** ako endpoint.
- **Skutočný priebeh:** zápis audit udalostí prebieha vnútorne pri operáciách; overenie reťazca cez service/testy, nie cez HTTP. Gap: bez HTTP nástroja na verify.

## Negatívne prípady (skutočný stav)
- Zlé heslo pri logine: **overené** 401 cez HTTP (`scripts/flow_smoke.py`).
- Prístup bez tokenu na status endpointy: aktuálne **200** (status endpointy nie sú chránené auth) - rozdiel oproti očakávaniu „bez tokenu 401“ pre doménové API; doménové chránené HTTP endpointy však neexistujú.
- Žiak nevidí cudzie dáta / rodič nevidí učiteľské poznámky / zlá rola 403 na doménových API: **logika a autorizácia overená v service/integračných/permisných testoch**, ale cez HTTP sa nedá reálne vykonať (chýbajú doménové endpointy). Zaznamenané ako medzera.

## Zhrnutie medzier toku
- End-to-end tok 1–8 je funkčný na úrovni **doménových služieb a DB + testov**, nie na úrovni **HTTP API a frontend dátových integrácií**.
- Kritická medzera pre produkciu: chýbajúce doménové REST endpointy (a tým aj FE napojenie) pre K-01..K-15 operácie; audit verify bez HTTP; status endpointy bez vynútenej autentizácie.
