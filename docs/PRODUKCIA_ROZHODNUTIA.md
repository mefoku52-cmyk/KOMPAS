# PRODUKCIA_ROZHODNUTIA (FÁZA 8.7)

Zoznam bodov, ktoré je potrebné reálne rozhodnúť alebo doplniť pred/pri produkčnej príprave. Nie sú to placeholdery - ide o otvorené alebo neúplné oblasti zistené auditom.

## 1. Databáza a prostredie
- **ROZHODNUTIE POTREBNÉ:** cieľová produkčná databáza a connection string (PostgreSQL ako cieľ podľa D1). Aktuálne beží vývoj/testy nad SQLite; `scripts/check_prod.sh` overuje PostgreSQL len ak je dostupné. Je potrebné zvoliť inštanciu, správu používateľov, sieťový prístup a `DATABASE_URL`.
- **ROZHODNUTIE POTREBNÉ:** stratégia migrácií v produkcii (kedy spúšťať `alembic upgrade head`, rollback postup) a pravidlo, že migrácie idú pred nasadením novej verzie.
- **ROZHODNUTIE POTREBNÉ:** správa tajomstiev (`JWT_SECRET_KEY`, DB heslá, prípadné API kľúče) - mimo gitu, cez bezpečné úložisko/ENV na cieľovej infraštruktúre; `.env` nesmie byť commitnutý.

## 2. Doménové HTTP API a frontend integrácia (kritická medzera)
- **ROZHODNUTIE/PRÁCA POTREBNÁ:** väčšina modulov K-01..K-15 nemá doménové REST endpointy (iba `/status` alebo prázdne routery) a frontend volá reálne len `/auth/login`. Je potrebné rozhodnúť rozsah a navrhnúť/implementovať HTTP kontrakt (request/response, authz) pre doménové operácie tak, aby zodpovedal service vrstve a `docs/api-contracts/openapi.json` sa stal úplným. Bez toho nie je možný skutočný end-to-end HTTP/UI tok zo `docs/FLOW.md`.
- **ROZHODNUTIE POTREBNÉ:** autentizácia/autorizačná politika pre status endpointy (aktuálne bez vynúteného tokenu) a jednotné vynucovanie deny-by-default na všetkých doménových cestách.
- **ROZHODNUTIE/PRÁCA POTREBNÁ:** vystavenie audit verify (alebo ekvivalentu) cez chránený administrátorský endpoint, ak sa má overiteľnosť reťazca robiť operatívne.

## 3. Nasadenie a infraštruktúra
- **ROZHODNUTIE POTREBNÉ (N7):** model nasadenia nebol schválený - žiadne externé nasadenie bez výslovného schválenia. Treba určiť cieľovú platformu, spôsob behu backendu (ASGI server, reverse proxy, TLS), hostovanie frontendu a správu statických súborov.
- **ROZHODNUTIE POTREBNÉ:** dostupnosť Redis/pgvector v produkcii podľa potreby modulov (D4 - za rozhraniami; aktuálne nie sú hard dependency v základnom toku).
- **ROZHODNUTIE POTREBNÉ:** konfigurácia CORS, rate limiting a bezpečnostných hlavičiek na úrovni aplikácie/proxy pre produkčné domény.

## 4. Frontend build a E2E
- **ROZHODNUTIE POTREBNÉ:** build toolchain na cieľovej platforme (aktuálny Termux workaround: Next 13.5.11, `.babelrc`, `swcMinify: false`, natívny SWC nedostupný; na štandardnej CI/prod platforme overiť build bez tohto obmedzenia).
- **ROZHODNUTIE POTREBNÉ:** E2E nástroj a prostredie (Playwright nespustiteľné v Termux/Android prostredí) - zvoliť a nakonfigurovať v prostredí, kde prejde plný prehliadačový flow.

## 5. Doménové a produktové otvorené body (prevzaté/konkrétne)
- **ROZHODNUTIE POTREBNÉ:** škála hodnotenia `GRADE_MIN=1`/`GRADE_MAX=9` je dočasná (otvorené z FÁZY 7) - potvrdiť finálnu škálu a dopad na dáta.
- **ROZHODNUTIE POTREBNÉ:** AI architektúra a poskytovatelia (`ModelProvider`/`NullProvider` pripravené, bez rozhodnutého providera) - výber, zmluvy, limity, bezpečnosť dát.
- **ROZHODNUTIE POTREBNÉ:** multi-tenant/`school_id` model nasadenia (pripravené v dátach) - prevádzková izolácia a onboarding škôl.
- **ROZHODNUTIE POTREBNÉ:** priorita zariadení a responzívne UI požiadavky pre cieľových používateľov.

## 6. Kvalita a prevádzka
- **ROZHODNUTIE/PRÁCA POTREBNÁ:** doplnenie chýbajúcich testov pre doménové HTTP endpointy hneď po ich implementácii (aktuálne 75 passed pokrýva service/integration logiku).
- **ROZHODNUTIE POTREBNÉ:** zálohovanie/obnova pre produkčnú DB, monitoring, logovanie a incident postup (súčasť FÁZY 14 v špecifikácii - vyžaduje cieľovú infraštruktúru).
