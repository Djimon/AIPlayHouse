(function () {
  const params = new URLSearchParams(window.location.search);
  const role = (params.get("role") || "player").toUpperCase();
  const serverBase = params.get("server") || "http://127.0.0.1:8000";
  let encounterId = params.get("encounter_id") || "";
  let token = params.get("token") || "";
  let ws = null;

  const el = (id) => document.getElementById(id);

  el("role").textContent = role;
  el("server").textContent = serverBase;
  el("encounter").textContent = encounterId || "-";
  el("joinEncounterId").value = encounterId;
  el("joinToken").value = token;

  if (role === "HOST") {
    el("hostPanel").classList.remove("hidden");
    el("playerPanel").classList.add("hidden");
  } else {
    el("playerPanel").classList.remove("hidden");
    el("hostPanel").classList.add("hidden");
  }

  function setError(message) {
    el("state").textContent = message;
  }

  function setState(state) {
    el("state").textContent = JSON.stringify(state, null, 2);
    el("encounter").textContent = state.id;
    renderPlayers(state);
  }

  function renderPlayers(state) {
    const list = el("playerList");
    if (!list) {
      return;
    }
    const players = Array.isArray(state.players) ? state.players : [];
    list.textContent = "";
    if (players.length === 0) {
      list.textContent = "Keine Spieler registriert.";
      return;
    }

    for (const player of players) {
      if (!player || typeof player !== "object") {
        continue;
      }
      const row = document.createElement("div");
      row.className = "player-row";

      const nameWrap = document.createElement("div");
      const nameText = document.createElement("div");
      nameText.className = "player-name";
      nameText.textContent = player.name || "Spieler";
      const idText = document.createElement("div");
      idText.className = "player-id";
      idText.textContent = player.id || "-";
      nameWrap.appendChild(nameText);
      nameWrap.appendChild(idText);

      const input = document.createElement("input");
      input.type = "number";
      input.min = "1";
      input.max = "99";
      if (typeof player.initiative === "number") {
        input.value = String(player.initiative);
      }

      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Set";
      button.disabled = role !== "HOST";
      button.onclick = async () => {
        if (role !== "HOST") {
          return;
        }
        const value = Number.parseInt(input.value, 10);
        if (Number.isNaN(value) || value < 1 || value > 99) {
          setError("Initiative muss zwischen 1 und 99 liegen.");
          return;
        }
        await postAction({ type: "SET_INITIATIVE", playerId: player.id, initiative: value });
      };

      row.appendChild(nameWrap);
      row.appendChild(input);
      row.appendChild(button);
      list.appendChild(row);
    }
  }

  function wsUrl(id, tok) {
    const base = new URL(serverBase);
    const proto = base.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${base.host}/ws/encounters/${id}?token=${encodeURIComponent(tok)}`;
  }

  async function requestJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  async function loadState(id, tok) {
    const data = await requestJson(
      `${serverBase}/api/encounters/${id}?token=${encodeURIComponent(tok)}`,
    );
    setState(data.state);
  }

  function connectWs(id, tok) {
    if (ws) {
      ws.close();
    }
    ws = new WebSocket(wsUrl(id, tok));
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "state.full") {
        setState(payload.state);
      }
    };
  }

  function setHostActionsEnabled(enabled) {
    el("nextTurnBtn").disabled = !enabled;
    el("addEffectBtn").disabled = !enabled;
    el("removeEffectBtn").disabled = !enabled;
    el("applyDamageBtn").disabled = !enabled;
    el("resolveConcentrationBtn").disabled = !enabled;
    el("applySaveBtn").disabled = !enabled;
  }

  function setPlayerActionsEnabled(enabled) {
    el("rollBtn").disabled = !enabled;
    el("chatBtn").disabled = !enabled;
    el("registerBtn").disabled = !enabled;
  }

  async function joinExisting() {
    encounterId = el("joinEncounterId").value.trim();
    token = el("joinToken").value.trim();
    if (!encounterId || !token) {
      setError("Encounter ID und Token benoetigt.");
      return;
    }
    await loadState(encounterId, token);
    connectWs(encounterId, token);
    setHostActionsEnabled(role === "HOST");
    setPlayerActionsEnabled(role === "PLAYER");
  }

  async function postAction(action) {
    const data = await requestJson(
      `${serverBase}/api/encounters/${encounterId}/actions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, action }),
      },
    );
    setState(data.state);
  }

  async function postRoll(kind) {
    const data = await requestJson(
      `${serverBase}/api/encounters/${encounterId}/rolls`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, roll: { kind } }),
      },
    );
    setState(data.state);
  }

  async function postChat(message) {
    const data = await requestJson(
      `${serverBase}/api/encounters/${encounterId}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, message }),
      },
    );
    setState(data.state);
  }

  async function registerPlayer() {
    const name = el("playerName").value.trim();
    if (!name) {
      setError("Spielername benoetigt.");
      return;
    }
    const data = await requestJson(
      `${serverBase}/api/encounters/${encounterId}/players`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, name }),
      },
    );
    setState(data.state);
  }

  el("createEncounterBtn").onclick = async () => {
    if (role !== "HOST") {
      return;
    }
    const response = await requestJson(`${serverBase}/api/encounters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: el("encounterName").value.trim() || "Session Local" }),
    });
    encounterId = response.encounter_id;
    token = response.host_token;
    el("hostToken").textContent = response.host_token;
    el("playerToken").textContent = response.player_token;
    el("joinEncounterId").value = encounterId;
    el("joinToken").value = token;
    await joinExisting();
  };

  el("joinBtn").onclick = async () => {
    try {
      await joinExisting();
    } catch (err) {
      setError(String(err));
    }
  };

  el("nextTurnBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    await postAction({ type: "NEXT_TURN" });
  };

  el("addEffectBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const effectId = el("effectId").value.trim();
    if (!effectId) {
      setError("Effect ID benoetigt.");
      return;
    }
    const effect = { id: effectId };
    const roundsRaw = el("effectRounds").value.trim();
    if (roundsRaw) {
      const rounds = Number.parseInt(roundsRaw, 10);
      if (!Number.isNaN(rounds)) {
        effect.roundsRemaining = rounds;
      }
    }
    const concentrationActorId = el("effectConcentrationActorId").value.trim();
    if (concentrationActorId) {
      effect.concentrationActorId = concentrationActorId;
    }
    const sourceActorId = el("effectSourceActorId").value.trim();
    if (sourceActorId) {
      effect.sourceActorId = sourceActorId;
    }
    if (el("effectRequiresConcentration").checked) {
      effect.requiresConcentration = true;
    }
    await postAction({ type: "ADD_EFFECT", effect });
  };

  el("removeEffectBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const effectId = el("effectId").value.trim();
    if (!effectId) {
      setError("Effect ID benoetigt.");
      return;
    }
    await postAction({ type: "REMOVE_EFFECT", effectId });
  };

  el("applyDamageBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const actorId = el("damageActorId").value.trim();
    const damageRaw = el("damageTaken").value.trim();
    const damageTaken = Number.parseInt(damageRaw, 10);
    if (!actorId || Number.isNaN(damageTaken) || damageTaken <= 0) {
      setError("Actor ID und positiver Schaden benoetigt.");
      return;
    }
    await postAction({ type: "APPLY_DAMAGE", actorId, damageTaken });
  };

  el("resolveConcentrationBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const actorId = el("concentrationActorId").value.trim();
    if (!actorId) {
      setError("Actor ID benoetigt.");
      return;
    }
    const success = el("concentrationResult").value === "success";
    await postAction({ type: "RESOLVE_CONCENTRATION_SAVE", actorId, success });
  };

  el("applySaveBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const effectId = el("saveEffectId").value.trim();
    if (!effectId) {
      setError("Effect ID benoetigt.");
      return;
    }
    const success = el("saveResult").value === "success";
    await postAction({ type: "APPLY_SAVE_RESULT", effectId, success });
  };

  el("rollBtn").onclick = async () => {
    if (role !== "PLAYER" || !encounterId) {
      return;
    }
    const kind = el("rollKind").value;
    await postRoll(kind);
  };

  el("chatBtn").onclick = async () => {
    if (role !== "PLAYER" || !encounterId) {
      return;
    }
    const text = el("chatText").value.trim();
    if (!text) {
      return;
    }
    await postChat(text);
    el("chatText").value = "";
  };

  el("registerBtn").onclick = async () => {
    if (role !== "PLAYER" || !encounterId) {
      return;
    }
    await registerPlayer();
  };

  setHostActionsEnabled(false);
  setPlayerActionsEnabled(false);

  if (encounterId && token) {
    joinExisting().catch((err) => {
      setError(String(err));
    });
  }
})();
