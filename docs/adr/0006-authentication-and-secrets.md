# ADR 0006 - D5: Autentifikacia a kryptograficke kniznice (spresnene)

- Stav: prijate (technicke rozhodnutie architekta, spresnene po nezavislym overeni)
- Datum: 2026-11-16

## Kontext
V prostredi Termux/Android nie je mozne spolahlivo nacitat kniznicu `cryptography` (chyba pri nacitani natívnej casti: `dlopen: cannot locate symbol PyBaseObject_Type`). Povodne uvazovane `python-jose[cryptography]` a `passlib` preto nie su pouzitelne.

## Rozhodnutie
- JSON Web Token (JWT): kniznica `PyJWT`, iba algoritmus HS256 (symetricky HMAC so SHA-256). Asymetricke algoritmy sa v tomto rozsahu nepouzivaju.
- Hashovanie hesiel: `argon2-cffi` (Argon2). Ziadna vlastna kryptografia.
- Kniznice `cryptography`, `python-jose`, `ecdsa`, `rsa` a `passlib` sa NESMU instalovat ani pridavat do `backend/requirements.txt`.
- Tajomstva (kluce, hesla) iba cez premenne prostredia; vzor v `.env.example`.

## Dosledky
- Implementacia autentifikacie musi pouzivat iba `PyJWT` (HS256) a `argon2-cffi`.
- Pri buducej zmene prostredia alebo potrebe asymetrickych algoritmov je nutne nove ADR a overenie kompatibility.
- Bezpecnostna kontrola overi, ze zakazane kniznice nie su v zavislostiach.
