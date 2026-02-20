# D&D Battle Tracker (V0) — PyWebView + lokal (2 Instanzen), FastAPI localhost, Postgres lokal

## Ziel
V0 als **lokal testbares** System mit:
- **PyWebView** als UI-Container (zwei Programm-Instanzen simulieren Host/Player)
- **FastAPI** als lokaler Server auf `localhost`
- **PostgreSQL lokal** als Persistenz
- **Autosave** nach jeder State-Änderung (Server ist *Source of Truth*)
- **WebSocket** für Live-Sync zwischen den Instanzen
- **Invite-Link / Join-Code** ohne Registrierung (rein lokal)

**Simulationsmodus:** Du startest das Programm zweimal:
- Instanz 1: Host-UI
- Instanz 2: Player-UI

---

## Festgelegte Regeln (aus den Vorgaben)
- **Zusammenarbeit über einen gemeinsamen lokalen Server** (Option 1A).
- **Persistenz bleibt PostgreSQL** (Option 2C).
- **Host ist die einzige Instanz, die Encounter-State ändern darf** (Option 3: ja).
- **Player darf würfeln + chatten** (keine State-Änderungen).
- **Sync:** WebSocket.
- **Initiative:** Host kann **manuell** setzen und/oder Tool kann würfeln (3C).
- **Concentration & Saves:** **ja** in V0 (wie V1).
- **Effect-Dauer „1 Runde“ tickt bei `round_end`** (global).
- Deployment: **rein lokal**, kein TLS nötig (`http://localhost`, `ws://localhost`).

---

## 1) Minimal-Architektur (lokal, ohne Webspace)

### 1.1 Prozesse (lokal)
Du hast drei Bausteine:
1. **FastAPI Server** (einmal pro Rechner)
2. **PyWebView App-Instanz #1** (Host)
3. **PyWebView App-Instanz #2** (Player)

**Wichtig:** Der Server läuft **einmal**, beide Instanzen verbinden sich dahin.

### 1.2 Datenfluss (Source of Truth = Server)
1. Client sendet:
   - **HOST:** `action` (z.B. `NEXT_TURN`, `APPLY_DAMAGE`)
   - **PLAYER:** `roll.submit` oder `chat.send`
2. Server validiert Token/Rolle.
3. Server führt **Reducer/Engine** aus (nur für Host-Actions).
4. Server speichert **Snapshot** in Postgres (**Autosave**).
5. Server broadcastet **Full State** an alle Clients per WS (V0).

### 1.3 Realtime-Sync
- **WebSocket** auf `ws://localhost:<port>/ws/encounters/{id}?token=...`
- V0: **Full-state Broadcast** (einfach, debugbar)

---

## 2) PyWebView Setup (V0)

### 2.1 UI-Strategie (minimal)
PyWebView zeigt eine lokale Web-UI (HTML/JS/CSS), die:
- per REST den aktuellen State lädt
- per WS live Updates erhält
- Host-Actions per REST sendet
- Player-Rolls/Chat per REST oder WS sendet

**Empfehlung für V0:**  
- REST für Actions/Rolls/Chat (einfach)  
- WS nur zum Broadcast `state.full`

### 2.2 Zwei Instanzen starten
Startargumente/Modus:
- `--role host`
- `--role player`
- optional: `--join <player_token>` oder `--host <host_token>`

V0 kann beim Start:
- Host-Modus: Encounter anlegen, Token ausgeben
- Player-Modus: Token eingeben oder per Clipboard übernehmen

---

## 3) Rollen- und Tokenmodell (lokal)

### 3.1 Rollen
- `HOST`: darf Actions ausführen (State verändern).
- `PLAYER`: darf nur:
  - Rolls submitten
  - Chat senden

### 3.2 Tokens / Join-Codes
Pro Encounter:
- `host_token` (geheim, volle Rechte)
- `player_token` (geheim, eingeschränkte Rechte)

V0 Usability-Variante:
- Host zeigt **Join-Code** (kurzer Code), der serverseitig auf `player_token` mapped  
  (optional; technisch kannst du auch direkt den langen Token nutzen)

**Speicherung:**
- DB speichert `token_hash = sha256(token + server_salt)`.

**Transport lokal:**
- Token als Query-Param oder Header bei REST
- WS connect: `?token=...`

---

## 4) Server State (V0 Datenmodell, identisch zu V1)

### 4.1 EncounterState (als JSON)
Der serverseitige State ist ein JSON-Dokument (versioniert).

**EncounterState**
- `id: string`
- `version: int`
- `status: "setup" | "running" | "ended"`
- `round: int` (start 1)
- `turnIndex: int`
- `turnOrder: string[]`
- `actors: Record<actorId, Actor>`
- `effects: Effect[]`
- `concentration: Record<actorId, ConcentrationState | null>`
- `chat: ChatMessage[]`
- `log: LogEntry[]` *(optional)*
- `meta: { name, createdAt, updatedAt }`

(Actor/Effect/Concentration/Chat/Log wie im V1-Dokument.)

---

## 5) PostgreSQL lokal (V0 Persistenz)

### 5.1 Tabellen (minimal, robust)
**`encounters`**
- `id uuid pk`
- `name text`
- `status text`
- `current_version int`
- `created_at timestamptz`
- `updated_at timestamptz`

**`encounter_tokens`**
- `id uuid pk`
- `encounter_id uuid fk`
- `role text` (`HOST`/`PLAYER`)
- `token_hash text unique`
- `created_at timestamptz`
- `revoked_at timestamptz null`

**`encounter_snapshots`**
- `id uuid pk`
- `encounter_id uuid fk`
- `version int`
- `created_at timestamptz`
- `state_json jsonb`
- `unique(encounter_id, version)`

**`encounter_rolls`** *(empfohlen)*
- `id uuid pk`
- `encounter_id uuid fk`
- `created_at timestamptz`
- `actor_id text null`
- `who_label text`
- `roll_json jsonb`

**`encounter_chat`** *(empfohlen)*
- `id uuid pk`
- `encounter_id uuid fk`
- `created_at timestamptz`
- `who_label text`
- `actor_id text null`
- `text text`

### 5.2 Autosave-Algorithmus
Bei jeder **Host-Action**:
1. Lade letzten Snapshot (oder `current_version`).
2. Reducer/Engine: `newState`, `version+1`.
3. Insert Snapshot.
4. Update `encounters.current_version`.
5. Broadcast Full State via WS.

Bei **Player-Roll/Chat**:
- Insert in `encounter_rolls` / `encounter_chat`
- zusätzlich in `state.chat`/`state.log` übernehmen und Snapshot schreiben (V0), damit Full State konsistent ist

---

## 6) API + WebSocket Protokoll (V0)

### 6.1 REST Endpoints
- `POST /api/encounters`
  - erstellt Encounter + Tokens
  - Response: `encounter_id`, `host_token`, `player_token` (für V0 ok lokal)
- `GET /api/encounters/{id}?token=...`
  - liefert aktuellen Full State
- `POST /api/encounters/{id}/actions`
  - **HOST only**
  - Body: `{ token, action }`
  - Response: `{ state }`
- `POST /api/encounters/{id}/rolls`
  - **PLAYER oder HOST**
  - Body: `{ token, roll }`
- `POST /api/encounters/{id}/chat`
  - **PLAYER oder HOST**
  - Body: `{ token, message }`

### 6.2 WebSocket
`GET /ws/encounters/{id}?token=...`

**Server → Client**
- `state.full` (initial)
- `state.full` (nach jeder Änderung)

**Client → Server** (optional; V0 kann alles via REST machen)
- `presence.hello` (Label setzen)

---

## 7) Reducer + Effect Engine (V0 Regeln, identisch zu V1)

### 7.1 Turn/Round Ablauf
`NEXT_TURN`:
1. `applyTiming(turn_end, currentActor)`
2. `advanceTurnIndex()`
3. Wenn wrap-around:
   - `applyTiming(round_end)`
   - **tick durations** (“1 Runde” runterzählen bei `round_end`)
   - entferne abgelaufene Effekte
   - `round += 1`
   - optional `applyTiming(round_start)`
4. `applyTiming(turn_start, newActor)`
5. persist + broadcast

### 7.2 Concentration
- Bei `APPLY_DAMAGE` auf concentrating Actor:
  - DC = `max(10, floor(damageTaken/2))`
  - Log/System-Flag „Concentration check needed“
- Player würfelt, Host wendet Ergebnis an:
  - `RESOLVE_CONCENTRATION_SAVE`

### 7.3 Saves (save_ends)
- Player würfelt Save, Host wendet Ergebnis an:
  - `APPLY_SAVE_RESULT`

---

## 8) Projektstruktur (V0, pragmatisch)

### 8.1 Repository Layout
- `server/`
  - `app/`
    - `main.py` (FastAPI app + routes)
    - `ws.py` (WS manager)
    - `engine/` (reducer + effect engine)
    - `db/` (queries + migrations)
    - `models/` (Pydantic schemas)
- `client/`
  - `ui/` (statische html/js/css oder kleines Vite bundle)
- `desktop/`
  - `launcher.py` (PyWebView старт)
  - startet optional den lokalen Server (siehe unten)

### 8.2 Server-Start (lokal)
Zwei Modi:
- **Manuell**: du startest `uvicorn` selbst
- **Integriert**: `launcher.py` startet Server-Subprozess, dann öffnet PyWebView

V0 Empfehlung:
- integriert, damit “Doppelklick startet alles”.

---

## 9) Tests (V0 minimal)
- Unit: Engine (Turnwechsel, round_end ticks, effect expiry, concentration DC)
- Integration: Snapshot persist + reload equals

---

## 10) Nächste Implementationspakete (V0)

### Paket 1 — Lokaler Server + DB
- Postgres local config
- Schema/Migration
- `POST /encounters`, `GET /encounters/{id}`

### Paket 2 — WebSocket Broadcast
- WS connect
- initial `state.full`
- broadcast bei Änderungen

### Paket 3 — PyWebView UI (Host/Player)
- Role-based UI
- connect/load state
- join token handling

### Paket 4 — Actions + Autosave
- `POST /actions` + engine
- snapshots + WS broadcast

### Paket 5 — Rolls + Chat
- `POST /rolls`, `POST /chat`
- persist + include in state

### Paket 6 — Effects + Concentration + Saves
- add/remove effects
- tick rules (round_end)
- resolve concentration/save flows

---

## Appendix: V0-Constraints
- V0 ist **lokal**: keine Accounts, kein TLS.
- Full State Broadcast (simpel).
- Host-only State-Commit.
- Player nur Roll+Chat.
