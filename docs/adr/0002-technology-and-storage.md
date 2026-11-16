# ADR 0002 - D1: Databaza a zdroj pravdy schemy

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Projekt potrebuje jednotny zdroj pravdy pre datovu schemu s podporou vyvoja v obmedzenom prostredi (Termux/Android) a cielovou produkcnou prevadzkou na PostgreSQL.

## Rozhodnutie
- SQLAlchemy 2.x (synchronny rezim) je jediny zdroj pravdy pre schemu.
- Cielova produkcna databaza je PostgreSQL.
- Vyvoj a testy bezia nad SQLite cez premennu prostredia `DATABASE_URL`.
- Kod nesmie pouzivat funkcie specificke pre jednu databazu mimo jednej dokumentovanej adapterovej vrstvy.

## Dosledky
- Modely musia byt kompatibilne s oboma dialektmi.
- Rozdiely (typy, spravanie) sa riesia v adapterovej vrstve, nie ad-hoc v moduloch.
