# ISSUE-06 Check gegen Konzept (`plan.md`) und Scope

## Referenz
- Issue: `dndtracker/issues/ISSUE-06-effects-concentration-saves.md`
- Konzept: `dndtracker/plan.md` (Abschnitte 7.1, 7.2, 7.3, 10 Paket 6)

## Vor Umsetzung: offene Punkte (Ist-Stand)

- [ ] Engine unterstützte nur `NEXT_TURN`; es fehlten dedizierte Action-Flows für:
  - `ADD_EFFECT`
  - `REMOVE_EFFECT`
  - `APPLY_DAMAGE`
  - `RESOLVE_CONCENTRATION_SAVE`
  - `APPLY_SAVE_RESULT`
- [ ] Concentration-Logik bei Schaden (DC `max(10, floor(damageTaken/2))`) war nicht umgesetzt.
- [ ] Auflösung des Concentration-Saves inkl. State-Änderung war nicht umgesetzt.
- [ ] Save-End-Flow (`APPLY_SAVE_RESULT`) war nicht umgesetzt.
- [ ] Unit-Tests für die neuen Engine-Flows fehlten.

## Umsetzungsschritte

1. Reducer-Dispatch in `apply_host_action` auf die Issue-06-Actiontypen erweitert.
2. Effektverwaltung ergänzt:
   - `ADD_EFFECT` hängt Effektdaten an,
   - `REMOVE_EFFECT` entfernt per `effectId`.
3. Concentration-Flow ergänzt:
   - `APPLY_DAMAGE` markiert bei konzentrierendem Actor `checkNeeded` und berechnet DC nach Spezifikation.
   - `RESOLVE_CONCENTRATION_SAVE` setzt bei Erfolg den Check zurück; bei Misserfolg wird Konzentration beendet und abhängige Effekte entfernt.
4. Save-Flow ergänzt:
   - `APPLY_SAVE_RESULT` entfernt den Effekt bei erfolgreichem Save reproduzierbar per `effectId`.
5. Unit-Tests in `tests/backend/unit/test_engine.py` ergänzt, um alle neuen Flows abzudecken.

## Rest-Status nach Umsetzung

- Für ISSUE-06 sind im definierten Scope keine offenen Punkte mehr vorhanden.
- `NEXT_TURN`-Ablauf inkl. `round_end`-Tick bleibt unverändert abgesichert.
- Concentration- und Save-Änderungen laufen über den bestehenden Host-Action-/Autosave-/Broadcast-Pfad aus ISSUE-04.
