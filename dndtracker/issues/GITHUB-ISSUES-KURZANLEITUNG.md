# GitHub-Issues anlegen – Kurz erklärt

## Was bedeutet `owner/repo`?

`owner/repo` ist der eindeutige Name eines GitHub-Repositories:

- `owner` = Benutzername **oder** Organisation auf GitHub
- `repo` = Repository-Name

Für dieses Projekt ist der Wert:

- `Djimon/AIPlayHouse`
- URL: `https://github.com/Djimon/AIPlayHouse.git`

## Zusammenhang mit diesem Projekt

Die vorbereiteten Dateien in `dndtracker/issues/` sind **Issue-Entwürfe**.
Damit sie als echte GitHub-Issues erstellt werden können, braucht ein Tool (z. B. `gh`) das Ziel-Repo im Format `owner/repo`.

## Direkter Befehl für dieses Repository

```bash
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-01: Server + DB Foundation" --body-file dndtracker/issues/ISSUE-01-server-db-foundation.md
```

## Alle 6 vorbereiteten Issues in Serie anlegen

```bash
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-01: Server + DB Foundation" --body-file dndtracker/issues/ISSUE-01-server-db-foundation.md
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-02: WebSocket Broadcast" --body-file dndtracker/issues/ISSUE-02-websocket-broadcast.md
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-03: PyWebView Host/Player UI" --body-file dndtracker/issues/ISSUE-03-pywebview-host-player-ui.md
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-04: Actions + Autosave Engine" --body-file dndtracker/issues/ISSUE-04-actions-autosave-engine.md
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-05: Rolls + Chat" --body-file dndtracker/issues/ISSUE-05-rolls-chat.md
gh issue create --repo Djimon/AIPlayHouse --title "ISSUE-06: Effects + Concentration + Saves" --body-file dndtracker/issues/ISSUE-06-effects-concentration-saves.md
```
