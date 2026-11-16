# ADR 0008 - D7: Preklady vo frontende

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Texty pre pouzivatela musia byt mimo kodu a zdieľane konzistentne.

## Rozhodnutie
- Frontend cerpa preklady z korenoveho adresara `locales/` (zdroj pravdy).
- Skript `scripts/sync_locales.sh` ich skopiruje do `frontend/src/locales` (adresar generovany, v `.gitignore`).

## Dosledky
- Editacia prekladov prebieha v korenovom `locales/`.
- Generovany ciel sa necommituje.
