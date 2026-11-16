# Katalóg udalostí

## Infraštruktúra
- Zbernica: `app.core.events.bus.EventBus` (typ `DomainEvent`: event_id, event_type, čas, school_id, payload).
- Perzistencia: `audit_event_log`, izolácia chýb handlera (log, publikujúci nespadne).

## Publikované/odoberané udalosti (aktuálny stav)
- `AnswerEvaluated` / `learning.answer_evaluated` - publikuje K-04 (vyhodnotenie pokusu), odoberá K-05 (zápis stavu témy: precvičené/čiastočne zvládnuté; overené zvládnutie len pri verifikačnom pokuse).
- Ostatné moduly v aktuálnom rozsahu bez doménových publikácií/odberov (registrujú handlery/routery).
