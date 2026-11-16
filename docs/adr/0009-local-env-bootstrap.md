# ADR 0009 - Lokalne prostredie (.env) a make_env.sh

- Stav: prijate (vynimka z pravidla 6 schvalena pouzivatelom)
- Datum: 2026-11-16

## Kontext
Testy a Alembic musia fungovat po nacitani lokalneho `.env`. Tajomstva sa nesmu commitovat do repozitara. Potrebny je opakovatelny sposob vytvorenia lokalneho suboru s nahodne vygenerovanym tajomstvom.

## Rozhodnutie
- `scripts/make_env.sh` vytvori lokalny `.env` z `.env.example` a doplni nahodne vygenerovane `JWT_SECRET_KEY` (bez prepisania existujuceho `.env`).
- `.env` sa nikdy necommituje (je v `.gitignore`).
- `.env.example` neobsahuje hodnoty tajomstiev.
- Aplikacia/testy/Alembic nacitavaju konfiguraciu z prostredia (podpora nacitania z `.env`).

## Dosledky
- Rychle a bezpecne lokalne spustenie bez ukladania tajomstiev do gitu.
- Nad ramec povoleneho zoznamu doplneni (5.3) je pridany `scripts/make_env.sh` ako schvalena vynimka.
