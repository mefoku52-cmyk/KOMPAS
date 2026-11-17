# ADR 0011 - Krátka platnosť prístupového tokenu a zneplatnenie

## Stav
Prijaté (FÁZA 9).

## Kontext
Prístupový JWT token nesie identitu, rolu a školu. Pri úniku tokenu alebo zmene hesla musí byť možné prístup okamžite ukončiť. Zároveň nechceme v tejto fáze zavádzať stavovú reláciu pre každý request ani obnovovacie tokeny, ktoré by vyžadovali ďalšiu infraštruktúru.

## Rozhodnutie
- Prístupový token má predvolenú platnosť 30 minút (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`), vydavateľa `JWT_ISSUER` a publikum `JWT_AUDIENCE`; podpis je HS256 (D5).
- Token obsahuje `jti`, `iat`, `exp`, `sub`, `role`, `school_id` a pri existujúcej zmene hesla aj `pwd_ts`.
- Odhlásenie zapíše `jti` do tabuľky `identity_revoked_token`; ďalšie requesty s týmto tokenom dostanú 401 `token_revoked`.
- Zmena hesla nastaví `password_changed_at`; tokeny bez zhodného `pwd_ts` prestanú platiť bez čakania na expiráciu.
- Obnovovací token sa v tejto fáze neimplementuje; po expirácii sa používateľ prihlási znova. Toto je vedomé obmedzenie, kým nebude rozhodnuté o reláciách a zariadeniach.

## Dôsledky
Kompromitovaný token má obmedzenú životnosť a zmena hesla zneplatní staré tokeny. Odhlásenie vyžaduje zápis do DB, čo je prijateľné pre očakávanú záťaž. Pri budúcom nasadení s viacerými inštanciami musí byť tabuľka revocation dostupná všetkým inštanciám.
