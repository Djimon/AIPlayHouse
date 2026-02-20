# ISSUE-05 — Rolls + Chat (Host/Player)

## Labels
`phase:v0` `type:feature` `priority:p2` `area:server` `area:db` `role:host` `role:player`

## Ziel
Roll- und Chat-Interaktionen für Host und Player inklusive Persistenz bereitstellen.

## Scope
- `POST /api/encounters/{id}/rolls`.
- `POST /api/encounters/{id}/chat`.
- Persistenz in `encounter_rolls` und `encounter_chat`.
- Eintrag zusätzlich in `state.chat`/`state.log` inkl. Snapshot schreiben, damit Full State konsistent bleibt.

## Akzeptanzkriterien
- Host und Player können Roll/Chat senden.
- Roll/Chat werden persistent gespeichert.
- Neue Clients sehen Roll/Chat im initialen Full State.

## Abhängigkeiten
- ISSUE-01.
- ISSUE-02.
- ISSUE-04.
