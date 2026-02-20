# ISSUE-04 — Host-Actions + Autosave + Engine-Basis

## Labels
`phase:v0` `type:feature` `priority:p1` `area:server` `area:engine` `role:host`

## Ziel
Host-Action-Flow mit Reducer-Ausführung, Snapshot-Autosave und Broadcast herstellen.

## Scope
- `POST /api/encounters/{id}/actions` (HOST only).
- Reducer/Engine-Aufruf für Host-State-Änderungen.
- Autosave-Flow:
  1. aktuellen Snapshot laden
  2. `version + 1`
  3. Snapshot speichern
  4. `encounters.current_version` aktualisieren
  5. `state.full` per WS broadcasten

## Akzeptanzkriterien
- Nur Host-Token kann Actions erfolgreich ausführen.
- Jede Action erzeugt einen neuen Snapshot mit inkrementierter Version.
- Verbundene Clients erhalten den aktualisierten Full State sofort.

## Abhängigkeiten
- ISSUE-01.
- ISSUE-02.
