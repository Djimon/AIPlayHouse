# ISSUE-01 — Lokaler Server + DB-Foundation

## Labels
`phase:v0` `type:feature` `priority:p1` `area:server` `area:db`

## Ziel
Lokal lauffähige Basis für FastAPI + PostgreSQL mit initialen Encounter-Endpunkten.

## Scope
- Lokale Postgres-Konfiguration für V0.
- Schema/Migration für:
  - `encounters`
  - `encounter_tokens`
  - `encounter_snapshots`
  - optional empfohlen: `encounter_rolls`, `encounter_chat`
- `POST /api/encounters`
  - erstellt Encounter + Tokens.
- `GET /api/encounters/{id}?token=...`
  - liefert aktuellen Full State.

## Akzeptanzkriterien
- Server startet lokal auf `localhost`.
- `POST /api/encounters` liefert `encounter_id`, `host_token`, `player_token`.
- `GET /api/encounters/{id}` liefert Snapshot mit aktuellem State.
- Token-Hashing wird verwendet (`sha256(token + server_salt)`).

## Abhängigkeiten
- Keine.
