# ADR 0014 - Odložené cudzie kľúče na PostgreSQL

## Stav
Prijaté pre FÁZU 10.

## Kontext
Modely zámerne nepoužívajú ORM relationship atribúty, takže SQLAlchemy Unit of Work nemá informácie o poradí závislostí medzi tabuľkami. SQLite porušenie cudzieho kľúča pred commitom nekontroluje, PostgreSQL áno. Testy aj seed skripty preto pri viacerých vkladaniach v jednej transakcii zlyhávali na poradí INSERTov, hoci výsledný stav transakcie bol konzistentný.

## Rozhodnutie
- Na PostgreSQL sa všetky cudzie kľúče vytvorené migráciami nastavujú ako `DEFERRABLE INITIALLY DEFERRED` migráciou `d4e5f6a7b8c9`.
- Kontrola zostáva povinná, ale vykoná sa pri COMMIT transakcie, keď sú všetky závislé riadky vložené.
- Testovacia fixture po `Base.metadata.create_all` aplikuje rovnaké nastavenie na novo vytvorené cudzie kľúče.
- SQLite sa nemení; obmedzenia tam zostávajú v pôvodnom režime.
- Downgrade migrácie vráti `NOT DEFERRABLE`.

## Dôsledky
- Konzistentný stav databázy je stále vynútený, ale porušenie FK sa prejaví až pri COMMIT, nie pri jednotlivom INSERTe.
- Kód nesmie spoliehať na okamžitú FK chybu uprostred transakcie; testy overujú konzistenciu po commitnutí.
- Ak sa v budúcnosti pridajú ORM relationships alebo explicitné flush poradie, deferral možno zúžiť iba na problémové tabuľky.
