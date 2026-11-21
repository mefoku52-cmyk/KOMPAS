# ADR 0015 - Retencia K-17 wellbeing pozorovani

## Stav
Prijaté.

## Kontext
K-17 ukladá behaviorálne pozorovania (čas na úlohu, chyby, odvodený stav) per žiak.
Tieto údaje sú osobné údaje v zmysle spracovania žiaka. Je potrebné vymedziť dobu
uchovávania a spôsob vynútenia.

## Rozhodnutie
- Doba uchovávania je konfigurovateľná cez `K17_RETENTION_DAYS` (predvolene 365 dní).
- Vynútenie zabezpečuje idempotentná úloha `purge_old_observations(db)` v
  `app.modules.k17_wellbeing_companion.tasks.processor`, ktorá vymaže záznamy staršie
  než konfigurovaná hranica. Úloha je bezpečná pri opakovanom spustení.
- Volí sa mazanie, nie anonymizácia: pozorovania sú viazané na konkrétneho žiaka
  a nevyužívajú sa pre dlhodobú anonymnú analytiku. Anonymizácia by vyžadovala
  zmenu schémy (nullable student_id) a stratu väzby na žiaka pre audit. Mazanie
  nezanecháva zvyšky osobných údajov.
- Úloha beží v rámci plánovaného spracovania počas nečinnosti (K-17 tasks).

## Dôsledky
- Po uplynutí lehoty sa pozorovania odstránia; audit log o prístupoch zostáva.
- Zmena lehoty je konfiguračná, bez migrácie.
