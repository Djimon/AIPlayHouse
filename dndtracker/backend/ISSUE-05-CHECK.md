# ISSUE-05 Check gegen Konzept (`plan.md`) und Scope

## Referenz
- Issue: `dndtracker/issues/ISSUE-05-rolls-chat.md`
- Konzept: `dndtracker/plan.md` (Abschnitte 5.2, 6.1, 10 Paket 5)

## Vor Umsetzung: offene Punkte (Ist-Stand)

- [x] Endpoint `POST /api/encounters/{id}/rolls` ist vorhanden.
- [x] Endpoint `POST /api/encounters/{id}/chat` ist vorhanden.
- [x] InMemory-Flow für Roll/Chat erhöht Version und schreibt in Snapshot-State (`state.log` / `state.chat`).
- [ ] Postgres-Flow `append_roll` war **nicht implementiert** (`NotImplementedError`).
- [ ] Postgres-Flow `append_chat` war **nicht implementiert** (`NotImplementedError`).
- [ ] Persistenz in `encounter_rolls` / `encounter_chat` für Postgres war damit offen.

## Umsetzungsschritte

1. Gemeinsame Snapshot-Mutationslogik vereinheitlicht (`_next_state_with_event` auf Modul-Ebene), damit Action/Roll/Chat in InMemory und Postgres konsistent den Full State fortschreiben.
2. `PostgresEncounterStore.append_roll` implementiert:
   - Token/Rolle validieren,
   - Roll in `encounter_rolls` speichern,
   - neuen Snapshot in `encounter_snapshots` speichern,
   - `encounters.current_version` und `updated_at` aktualisieren.
3. `PostgresEncounterStore.append_chat` implementiert:
   - Token/Rolle validieren,
   - Chat in `encounter_chat` speichern,
   - neuen Snapshot in `encounter_snapshots` speichern,
   - `encounters.current_version` und `updated_at` aktualisieren.
4. Tests ergänzt (API + Store), um Host/Player Roll/Chat sowie Postgres-Persistenzpfad und Snapshot-Fortschreibung abzudecken.

## Rest-Status nach Umsetzung

- Für ISSUE-05 sind laut definiertem Scope und Akzeptanzkriterien keine offenen Punkte mehr vorhanden.
- Roll/Chat sind für Host/Player nutzbar, werden persistent abgelegt und sind über den aktuellen Snapshot im initialen Full State sichtbar.

## Test-Discovery Konsistenz

- Importpfade für `backend`-Module wurden auf paketinterne relative Imports umgestellt, damit `python -m unittest -v` im Verzeichnis `dndtracker/` keine `ModuleNotFoundError` mehr durch absolute `dndtracker.*`-Imports wirft.
- `tests/__init__.py` wurde ergänzt, damit `unittest` die Testmodule im Ordner `tests/` bei Standard-Discovery zuverlässig findet.
