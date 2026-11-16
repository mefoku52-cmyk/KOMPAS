# ADR 0005 - D4: Cache/fronta a znalostny index

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Redis a vektorove vyhladavanie (pgvector) nemusia byt dostupne v cielovom vyvojovom prostredi.

## Rozhodnutie
- Redis a pgvector su za rozhraniami (cache/fronta, KnowledgeIndex).
- Predvolene implementacie su v procese: in-memory fronta, vyhladavanie klucovych slov nad schvalenymi dokumentmi.
- Plnohodnotny pgvector je mimo rozsahu, kym nebude PostgreSQL s potrebnymi rozsirenami k dispozicii.

## Dosledky
- Moduly zavisia od rozhrani, nie od konkretnej technologie.
- Prechod na Redis/pgvector nevyzaduje zmenu domenovej logiky.
