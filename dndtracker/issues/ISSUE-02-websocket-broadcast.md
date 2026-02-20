# ISSUE-02 — WebSocket Live-Sync (Full State Broadcast)

## Labels
`phase:v0` `type:feature` `priority:p1` `area:websocket` `area:server`

## Ziel
Live-Synchronisierung zwischen Host- und Player-Instanz über WebSocket.

## Scope
- `GET /ws/encounters/{id}?token=...` implementieren.
- Beim Connect initiales `state.full` senden.
- Bei jeder State-Änderung `state.full` an alle verbundenen Clients broadcasten.
- Token-/Rollenvalidierung beim WS-Connect.

## Akzeptanzkriterien
- Zwei lokale Clients sehen denselben State ohne manuellen Reload.
- Neuer Client bekommt sofort den aktuellen Full State.
- Ungültige Tokens werden abgewiesen.

## Abhängigkeiten
- ISSUE-01.
