# ADR 0010 - Spoločné API utility pre doménové endpointy

## Stav
Prijaté (FÁZA 9).

## Kontext
FÁZA 8 zistila, že moduly K-01 až K-16 majú doménovú logiku v službách, ale ich HTTP routery vystavujú iba `/status` alebo nemajú žiadne cesty. FÁZA 9 musí doplniť tenké doménové endpointy. Bez spoločnej serializácie a stránkovania by každý router duplikoval rovnaký kód a vznikali by nekonzistentné tvary odpovedí.

## Rozhodnutie
Zavádzame `backend/app/core/api.py` s:
- `serialize` - deterministický prevod SQLAlchemy modelov, UUID, dátumov a enumov do JSON kompatibilných hodnôt,
- `page_params` - jednotné stránkovanie s predvoleným limitom 50 a horným limitom 200,
- `paginated` - jednotný obal zoznamových odpovedí `{items, total, limit, offset}`.

Routers zostávajú tenké: validácia v Pydantic modeloch, volanie služby, serializácia. Obchodná logika, autorizácia a audit zostávajú v službách modulov.

## Dôsledky
- Konzistentný kontrakt pre frontend a testy.
- Horný limit stránky je vynútený na všetkých zoznamových endpointoch.
- Nový súbor je jediná výnimka z pravidla o nových súboroch pre túto oblasť; je zdôvodnený týmto ADR.
