# ISSUE-04 Check gegen Konzept (`plan.md`) und Scope

## Referenz
- Issue: `issues/ISSUE-04-actions-autosave-engine.md`
- Konzept: `plan.md` (Abschnitte 5.2, 6.1, 7.1, 10 Paket 4)

## Abgleich

- [x] Endpoint `POST /api/encounters/{id}/actions` ist vorhanden.
- [x] Endpoint ist Host-only (Player-Token wird mit 403 abgelehnt).
- [x] Reducer/Engine-Aufruf für Host-Actions ist angebunden.
- [x] `NEXT_TURN`-Ablauf mit Turn-/Round-Fortschritt ist in der Engine umgesetzt.
- [x] Jede erfolgreiche Action erzeugt einen neuen Snapshot-State mit inkrementierter Version.
- [x] Nach erfolgreicher Action wird `state.full` per WebSocket an verbundene Clients broadcastet.
- [x] Postgres-Autosave-Flow für Actions ist umgesetzt:
  1. aktueller Snapshot wird geladen (über Access-Lookup)
  2. `version + 1`
  3. Snapshot wird gespeichert
  4. `encounters.current_version` wird aktualisiert

## Rest-Status

- Für ISSUE-04 sind laut definiertem Scope und Akzeptanzkriterien keine offenen Punkte mehr vorhanden.
- Nicht Teil von ISSUE-04 und weiterhin separat offen:
  - Persistente Roll-/Chat-Mutationspfade in `PostgresEncounterStore` (ISSUE-05).
  - Erweiterte Effekt-/Concentration-/Save-Regeln (ISSUE-06).
