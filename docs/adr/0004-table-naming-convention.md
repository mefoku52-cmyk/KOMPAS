# ADR 0004 - D3: Konvencia nazvov tabuliek

- Stav: prijate (technicke rozhodnutie architekta)
- Datum: 2026-11-16

## Kontext
Modularny monolit vyzaduje jasnu prislusnost dat k oblastiam a overitelnost hranic.

## Rozhodnutie
- Prefix tabulky podla datovej oblasti: `identity_`, `school_`, `curriculum_`, `learning_`, `progress_`, `teacher_workspace_`, `organization_`, `communication_`, `ai_knowledge_`, `audit_`.
- Kazda tabulka patri presne jednej oblasti.
- Prislusnost sa overi automatickym testom; vsetkych 10 oblasti je pokrytych subormi v `db/schema`.

## Dosledky
- Nazvy tabuliek su strojovo kontrolovatelne.
- Skrizenie oblastí sa riesi navrhom dat, nie porusenim konvencie.
