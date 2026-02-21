# Analyse: D&D-Fixierung vs. System-Portabilität (basierend auf `plan.md` und aktuellem Code)

## 1) Kurzfazit

Der aktuelle Stand ist **regelmechanisch deutlich D&D-zentriert**, aber **architektonisch teilweise generisch**.

- Generisch: Client/Server-Sync, Token/Rollenmodell, Snapshot-Persistenz, WS-Broadcast, Action-Pipeline.
- D&D-fixiert: Konzentrationslogik, feste Save-/Effect-Semantik, Runden-Tick-Regel, vordefinierte Action-Typen und Felder.

Damit ist das Projekt derzeit eher ein **D&D Encounter Engine Scaffold** als eine systemagnostische PnP-Engine.

---

## 2) Wo es aktuell hart auf D&D fixiert ist

### 2.1 Harte D&D-Regeln im Reducer

Im Engine-Code sind D&D-Regeln direkt codiert:

- `APPLY_DAMAGE` setzt Concentration-DC als `max(10, damageTaken // 2)`.
- `RESOLVE_CONCENTRATION_SAVE` entfernt concentration-gebundene Effekte.
- `APPLY_SAVE_RESULT` modelliert ein `save_ends`-Muster.
- `NEXT_TURN` enthält fixen Ablauf mit `turn_end`, `round_end`, `round_start` und Runden-Ticks.

Diese Logiken sind keine neutralen Framework-Hooks, sondern regelwerksspezifische Entscheidungen.

### 2.2 D&D-nahe State-Semantik

Der State enthält Felder, die ein bestimmtes Regeldenken voraussetzen:

- `concentration` als eigener Top-Level-Bereich.
- `effects[].roundsRemaining` als primäre Ablaufsteuerung.
- implizite Annahme „1 Runde tickt am `round_end`“.

Das ist kompatibel mit 5e-artigen Abläufen, aber nicht neutral für Systeme ohne Initiative-Runden, mit Segment-/Phase-Strukturen oder ohne Concentration-Konzept.

### 2.3 UI/Workflow ist auf Encounter/Initiative-Schleife ausgerichtet

Die UI kennt fest `NEXT_TURN` als zentrale Host-Aktion. Das begünstigt rundenbasierte Kampfsysteme und passt schlechter zu:

- konfliktfreien, narrativen Szenen
- simultanen Systemen
- Systeme mit wechselnden Zeitachsen (z. B. Zonen-/Countdown-Modelle)

---

## 3) Was bereits systemagnostisch ist

- **Netzwerk-/Synchronisationsmodell:** REST + WS Full-State Broadcast.
- **Rollenmodell:** Host (autoritativ) vs. Player (eingeschränkt).
- **Persistenzmodell:** Versionierte Snapshots in JSONB.
- **Event-/Action-Prinzip:** Host sendet Actions, Server reduziert zu neuem State.

Diese Schichten sind gut wiederverwendbar und ein stabiles Fundament für mehrere Regelwerke.

---

## 4) Kernunterschiede zwischen D&D und „anderen PnP-Systemen“

Für Portabilität sind primär diese Achsen relevant:

1. **Initiative-/Zeitmodell**
   - D&D: lineare Turn Order + Runden.
   - Andere: Phasen, simultan, Slots, „Popcorn Initiative“, gar keine starre Reihenfolge.

2. **Effekt-Lebensdauer**
   - D&D: häufig rundenbasiert (`round_end`, `turn_start` etc.).
   - Andere: Szenenende, Trigger-basiert, Erfolg/Misserfolg, Ressourcenverbrauch.

3. **Defensiv-/Rettungsmechanik**
   - D&D: Save/DC-Struktur und concentration checks.
   - Andere: opposed rolls, fixed target numbers, stress/clock-Systeme, keine Saves.

4. **Schadens- und Zustandsmodell**
   - D&D: HP-zentriert, klar getrennte Conditions/Effects.
   - Andere: Wounds, Harm-Tiers, narrative Konsequenzen, Tags.

5. **Autorisierung von Aktionen**
   - Aktuell: Host-only für State-Commit.
   - Manche Systeme profitieren von co-authoring/GM-less Flows oder delegierten Rechten.

---

## 5) Was man umbauen sollte, um es elegant via JSON konfigurierbar zu machen

## 5.1 Zielbild

Trenne strikt:

- **Core Engine Runtime (generisch):** Action-Dispatch, State-Versionierung, Persistenz, WS/REST.
- **Ruleset Package (JSON + optionale Rule-Handler):** Zeitmodell, Aktionen, Validierung, Effekt-Ticks, Spezialregeln.

### 5.2 Konfigurierungs-Schichten

1. **`system.json` (Metadaten + aktivierte Module)**
   - `systemId`, `version`, `capabilities`, `timingModel`, `actionSet`.

2. **`state_schema.json` (strukturierte State-Definition)**
   - Pflichtfelder, optionale Bereiche, Validierungsregeln.

3. **`actions.json` (Action-Verträge)**
   - pro Action: Payload-Schema, Berechtigungen, erlaubte Pre-Conditions.

4. **`timing.json`**
   - wann Effekte ticken (`turn_start`, `round_end`, custom phases).

5. **`derived_rules.json`**
   - deklarative Regeln, z. B. „onDamage -> check X“.
   - bei komplexen Regeln: referenzierte Plugin-Handler (`python` entrypoints).

### 5.3 Konkrete Refactor-Schritte

1. **Action-Registry einführen**
   - Ersetze `if action_type == ...` durch Registry-Lookup.
   - Jeder Action-Handler hängt an einem deklarativen Action-Contract.

2. **Concentration aus Core entfernen**
   - als optionales Ruleset-Modul kapseln (z. B. `module_concentration`).

3. **Timing-Engine parametrierbar machen**
   - Tick-Punkte nicht hart in `NEXT_TURN`, sondern über `timingModel`.

4. **State-Hardcoding reduzieren**
   - `build_initial_state` aus Schema/Defaults generieren.
   - Systemfelder namespacen, z. B. `rules.<module>` statt Top-Level-Sonderfelder.

5. **Validierungsschicht vor Reducer**
   - JSON Schema/Pydantic dynamisch pro Ruleset laden.

6. **UI dynamisieren**
   - Buttons/Forms aus `actions.json` rendern (mind. teilweise), nicht nur `NEXT_TURN` fest verdrahten.

7. **Versionierung hart etablieren**
   - jedes Ruleset/Schema mit SemVer; Breaking changes erzwingen Migration.

### 5.4 Was JSON allein nicht leisten kann

- Reine JSON-Konfig reicht für einfache deklarative Regeln.
- Für komplexe Mechaniken (mehrstufige opposed rolls, Sondertrigger) braucht es:
  - **Rule-Plugins** (Python-Handler)
  - aber weiterhin durch JSON aktiviert/parametriert.

Empfehlung: **JSON-first, Plugin-escape hatch**.

---

## 6) Migrationsstrategie (inkrementell, risikoarm)

1. `dnd5e` als erstes explizites Ruleset extrahieren (ohne Verhaltensänderung).
2. Core-Interfaces stabilisieren (`ActionHandler`, `TimingHook`, `StateSchemaProvider`).
3. Bestehende Tests in zwei Klassen teilen:
   - Core-agnostische Tests
   - `dnd5e`-spezifische Tests
4. Zweites minimalistisches Referenz-Ruleset hinzufügen (z. B. „generic narrative“), um echte Portabilität zu validieren.

---

## 7) Bewertung „andere PnP-Systeme damit DM-bar?“

- **Heute:** eingeschränkt ja, wenn das Zielsystem nahe an D&D-Kampfloop liegt.
- **Heute nicht elegant:** Systeme mit anderem Zeit-, Save-, Effekt- oder Autoritätsmodell.
- **Nach Refactor:** gut machbar, wenn Core + Ruleset sauber getrennt und Actions/Timing/State über JSON + optionale Plugins definiert sind.
