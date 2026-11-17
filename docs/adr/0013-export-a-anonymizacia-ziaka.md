# ADR 0013 - Export údajov žiaka a hranice anonymizácie

## Stav
Prijaté pre export (FÁZA 9); anonymizácia a vymazanie sú iba návrh.

## Kontext
Žiak, zákonný zástupca a vedenie školy potrebujú získať údaje o žiakovi v prenosnom formáte. Súčasne platí, že osobné údaje sa nesmú sprístupniť neoprávnene a každý prístup musí byť dohľadateľný. Prompt výslovne zakazuje implementovať anonymizáciu a vymazanie bez samostatného schválenia.

## Rozhodnutie
- Export je dostupný cez `GET /privacy/students/{student_user_id}/export?purpose=...`.
- Oprávnené roly: žiak sám za seba, rodič s platným `identity_guardian_link` na dieťa, vedenie školy v tej istej škole. Učiteľ a cudzia škola dostanú 403.
- Účel exportu je povinný a ukladá sa do audit záznamu spolu s akciou `privacy.export_student_data`.
- Export obsahuje identitu bez hesla, roly, zápisy, učebné profily, stavy tém a pokusy o úlohy. Neobsahuje tajomstvá ani interné heše.
- Anonymizácia a vymazanie sa v tejto fáze NEIMPLEMENTUJÚ; vyžadujú právne rozhodnutie a samostatný ADR.

## Dôsledky
Export je auditovateľný a obmedzený na minimum potrebných rolí. Prípadná budúca anonymizácia musí doplniť vzťahy medzi auditom, históriou a zákonnými lehotami.
