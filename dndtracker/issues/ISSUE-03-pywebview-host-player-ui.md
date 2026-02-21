# ISSUE-03 — PyWebView UI für Host/Player

## Labels
`phase:v0` `type:feature` `priority:p1` `area:desktop` `area:ui` `role:host` `role:player`

## Ziel
Zwei lokale Programm-Instanzen als Host- und Player-UI nutzbar machen.

## Scope
- `desktop/launcher.py` mit lokalem Startfluss.
- Host-Modus:
  - Encounter erstellen.
  - Join-Token/Join-Code anzeigen.
- Player-Modus:
  - Token eingeben/übernehmen.
  - Encounter beitreten.
- Rollenbasierte UI:
  - Host kann State-Actions auslösen.
  - Player nur Roll + Chat.

## Akzeptanzkriterien
- Anwendung kann zweimal gestartet werden (Host + Player).
- Beide Instanzen verbinden sich auf denselben lokalen Server.
- UI-Rechte folgen strikt den Rollen.

## Abhängigkeiten
- ISSUE-01.
- ISSUE-02.

## Status-Hinweis (Implementierungsstand)
- Der aktuelle Stand nutzt für Mutationen noch den In-Memory-Store.
- PostgreSQL-Mutationen/Snapshots sind noch nicht umgesetzt und müssen in den nachfolgenden Server/Engine-Issues auf Postgres migriert werden.
- Die bestehenden `PostgresEncounterStore`-Mutationspfade sind derzeit noch `NotImplementedError`.

