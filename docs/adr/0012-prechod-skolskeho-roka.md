# ADR 0012 - Prechod školského roka

## Stav
Prijaté (FÁZA 9).

## Kontext
Škola potrebuje posunúť zápisy žiakov do nového školského roka bez straty histórie. Existujúci model `school_enrollment` je unikátny pre dvojicu `(school_year_id, student_user_id)`, takže nový rok vyžaduje nové záznamy a staré musia zostať čitateľné. Žiaci na najvyššom ročníku (`GRADE_MAX`) odchádzajú ako absolventi.

## Rozhodnutie
Prechod implementuje `backend/app/core/rollover.py`:
- pre každú triedu zdrojového roka sa vytvorí alebo znovu použije trieda v cieľovom roku s rovnakým názvom a ročníkom o jeden vyšším,
- žiakom sa vytvorí nový zápis v cieľovom roku, staré zápisy sa nemenia,
- žiaci v triede s ročníkom `GRADE_MAX` sa nezapisujú a počítajú sa ako absolventi,
- operácia je idempotentná: existujúce cieľové zápisy sa preskočia a triedy sa nezdvojujú,
- vstupom sú `school_id`, `from_school_year_id`, `to_school_year_id`; predvolený `GRADE_MAX` sa berie z konfigurácie.

## Dôsledky
História zostáva čitateľná, prechod možno bezpečne spustiť opakovane. Zmeny vykonáva administrátor cez `scripts/manage.py rollover-school-year`; operácia sa audituje.
