# ISSUE-06 — Effects, Concentration, Saves

## Labels
`phase:v0` `type:feature` `priority:p2` `area:engine` `area:server` `role:host` `role:player`

## Ziel
V0-Regeln für Effekte, Concentration und Saving Throws im Engine-Flow umsetzen.

## Scope
- Effektverwaltung (add/remove).
- Tick-Regel: Dauer „1 Runde“ reduziert bei `round_end`.
- Ablaufen von Effekten bei Dauer 0.
- Concentration-Flow:
  - Bei `APPLY_DAMAGE`: DC `max(10, floor(damageTaken/2))`.
  - Markierung „Concentration check needed“.
  - Host löst Ergebnis via `RESOLVE_CONCENTRATION_SAVE` auf.
- Saves (`save_ends`) via `APPLY_SAVE_RESULT`.

## Akzeptanzkriterien
- `NEXT_TURN` folgt definiertem Ablauf inkl. `round_end`-Tick.
- Concentration-DC und Auflösung verhalten sich gemäß Spezifikation.
- Save-Ergebnisse verändern den State reproduzierbar.

## Abhängigkeiten
- ISSUE-04.
- ISSUE-05.
