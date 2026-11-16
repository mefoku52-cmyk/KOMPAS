# ADR 0007 - D6: Subory a media

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Moduly (napr. kniznica, odovzdania) potrebuju ukladat subory bez viazanosti na konkretny backend uloziska.

## Rozhodnutie
- Subory a media su pristupne cez rozhranie `FileStorage` s lokalnou implementaciou (adresar mimo gitu).
- S3-kompatibilna implementacia je mimo rozsahu.

## Dosledky
- Cesty a ulozisko su abstrahovane; lokalny adresar musi byt v `.gitignore` (napr. `.data/`).
