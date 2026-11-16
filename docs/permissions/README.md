# Matica oprávnení

Zdroj pravdy pre automatický test `backend/tests/test_permissions_matrix.py` (krok 7.2).
Predvolené pravidlo: deny-by-default (`core/permissions/policy.py`).

## Rozsahy (Scope)
- `SELF` - vlastník/žiak sám sebe.
- `GUARDIAN_OF` - rodič iba pre prepojené dieťa (väzba `identity_guardian_link`).
- `TEACHES_CLASS` - učiteľ iba pre žiaka v triede, ktorú učí (priradenie k triede).
- `SCHOOL_AGGREGATE` - vedenie školy, agregované údaje v rámci školy.
- `SCHOOL_INDIVIDUAL_WITH_PURPOSE` - vedenie školy, individuálne údaje iba s uvedeným účelom (účel sa audituje).

## Viditeľnosť (Visibility)
- `TEACHER_PRIVATE_NOTE` - viditeľné iba učiteľovi-vlastníkovi; rodič ani iné roly nie.
- `PARENT_PRIVATE_COMMUNICATION` - viditeľné iba účastníkom súkromnej komunikácie.

## Matica (rola, zdroj/akcia, kontext) -> očakávanie
| rola | zdroj/akcia | kontext | výsledok |
|---|---|---|---|
| student | čítanie vlastného progresu | SELF, owner=student | povolené |
| student | čítanie cudzieho progresu | SELF, owner=iný | zamietnuté |
| parent | čítanie údajov dieťaťa | GUARDIAN_OF, prepojené dieťa | povolené |
| parent | čítanie údajov neprepojeného dieťaťa | GUARDIAN_OF, bez väzby | zamietnuté |
| teacher | čítanie žiaka triedy | TEACHES_CLASS, priradený k triede | povolené |
| teacher | čítanie žiaka inej triedy | TEACHES_CLASS, nepriradený | zamietnuté |
| leadership | agregáty školy | SCHOOL_AGGREGATE, vlastná škola | povolené |
| leadership | individuálne údaje s účelom | SCHOOL_INDIVIDUAL_WITH_PURPOSE, účel vyplnený | povolené |
| leadership | individuálne údaje bez účelu | SCHOOL_INDIVIDUAL_WITH_PURPOSE, účel prázdny | zamietnuté |
| teacher (vlastník) | súkromná poznámka učiteľa | TEACHER_PRIVATE_NOTE, owner=teacher | povolené |
| parent | súkromná poznámka učiteľa | TEACHER_PRIVATE_NOTE | zamietnuté |
| student | súkromná poznámka učiteľa | TEACHER_PRIVATE_NOTE | zamietnuté |
| účastník (parent) | súkromná komunikácia rodiča | PARENT_PRIVATE_COMMUNICATION, je účastník | povolené |
| teacher (neúčastník) | súkromná komunikácia rodiča | PARENT_PRIVATE_COMMUNICATION, nie je účastník | zamietnuté |
| student | agregáty školy | SCHOOL_AGGREGATE | zamietnuté |
| parent | triedny prehľad učiteľa | TEACHES_CLASS | zamietnuté |
| student | bez kontextu | žiadny scope/visibility | zamietnuté (deny-by-default) |
