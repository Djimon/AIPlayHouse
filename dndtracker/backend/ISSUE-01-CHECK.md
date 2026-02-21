# ISSUE-01 Check gegen Konzept (`plan.md`) und Scope

## Referenz
- Issue: `dndtracker/issues/ISSUE-01-server-db-foundation.md`
- Konzept: `dndtracker/plan.md` (Abschnitt 5 und 6)

## Abgleich

- [x] `POST /api/encounters` liefert `encounter_id`, `host_token`, `player_token`.
- [x] `GET /api/encounters/{id}?token=...` liefert aktuellen Full State.
- [x] Token-Hashing verwendet `sha256(token + server_salt)`.
- [x] SQL-Schema für `encounters`, `encounter_tokens`, `encounter_snapshots` vorhanden.
- [x] Optional empfohlene Tabellen `encounter_rolls`, `encounter_chat` vorhanden.
- [x] Lokale Postgres-Konfiguration über Env (`.env.example`) definiert.
- [x] Migration für lokales Postgres vorhanden (`python -m dndtracker.backend.migrate`).
- [x] Server ist lokal startbar (`uvicorn dndtracker.backend.api:app --host 127.0.0.1 --port 8000`).

## Hinweise zur aktuellen Implementierung

- Persistenz nutzt Postgres, sobald `DNDTRACKER_DATABASE_URL` gesetzt ist; ohne URL wird In-Memory genutzt.
- Fokus entspricht ISSUE-01 (Foundation). WebSocket/Actions/Rolls/Chat folgen in späteren Issues.
