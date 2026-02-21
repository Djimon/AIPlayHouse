# ISSUE-02 Check gegen Konzept (`plan.md`) und Scope

## Referenz
- Issue: `dndtracker/issues/ISSUE-02-websocket-broadcast.md`
- Konzept: `dndtracker/plan.md` (Abschnitte 1.3, 6.2, 10 Paket 2)

## Kurzabgleich

- [x] WS-Endpoint `GET /ws/encounters/{id}?token=...` ist implementiert.
- [x] Token-Validierung erfolgt beim Connect (ungültig/missing Token wird mit Close 1008 abgewiesen).
- [x] Nach erfolgreichem Connect wird initial `state.full` gesendet.
- [x] Bei State-Änderungen wird `state.full` an alle verbundenen Clients broadcastet.

## Rest-Status

- Für ISSUE-02 sind im definierten Scope keine offenen Punkte erkennbar.
