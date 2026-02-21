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

  function setState(state) {
    el("state").textContent = JSON.stringify(state, null, 2);
    el("encounter").textContent = state.id;
  }

  function wsUrl(id, tok) {
    const base = new URL(serverBase);
    const proto = base.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${base.host}/ws/encounters/${id}?token=${encodeURIComponent(tok)}`;
  }

  async function loadState(id, tok) {
    const response = await fetch(
      `${serverBase}/api/encounters/${id}?token=${encodeURIComponent(tok)}`,
    );
    if (!response.ok) {
      throw new Error(`GET state failed: ${response.status}`);
    }
    const data = await response.json();
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

  async function joinExisting() {
    encounterId = el("joinEncounterId").value.trim();
    token = el("joinToken").value.trim();
    if (!encounterId || !token) {
      return;
    }
    await loadState(encounterId, token);
    connectWs(encounterId, token);
    el("rollBtn").disabled = false;
    el("chatBtn").disabled = false;
    if (role === "HOST") {
      el("hostActionBtn").disabled = false;
    }
  }

  el("createEncounterBtn").onclick = async () => {
    if (role !== "HOST") {
      return;
    }
    const response = await fetch(`${serverBase}/api/encounters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: el("encounterName").value.trim() || "Session Local" }),
    });
    const created = await response.json();
    encounterId = created.encounter_id;
    token = created.host_token;
    el("hostToken").textContent = created.host_token;
    el("playerToken").textContent = created.player_token;
    el("joinEncounterId").value = encounterId;
    el("joinToken").value = token;
    await joinExisting();
  };

  el("joinBtn").onclick = async () => {
    await joinExisting();
  };

  el("hostActionBtn").onclick = async () => {
    if (role !== "HOST" || !encounterId) {
      return;
    }
    const response = await fetch(`${serverBase}/api/encounters/${encounterId}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, action: { type: "NEXT_TURN" } }),
    });
    const data = await response.json();
    setState(data.state);
  };

  el("rollBtn").onclick = async () => {
    if (!encounterId) {
      return;
    }
    const response = await fetch(`${serverBase}/api/encounters/${encounterId}/rolls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, roll: { kind: "d20", value: 14 } }),
    });
    const data = await response.json();
    setState(data.state);
  };

  el("chatBtn").onclick = async () => {
    if (!encounterId) {
      return;
    }
    const text = el("chatText").value.trim();
    if (!text) {
      return;
    }
    const response = await fetch(`${serverBase}/api/encounters/${encounterId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, message: text }),
    });
    const data = await response.json();
    setState(data.state);
    el("chatText").value = "";
  };

  if (role !== "HOST") {
    el("createEncounterBtn").disabled = true;
    el("hostActionBtn").disabled = true;
  }

  if (encounterId && token) {
    joinExisting().catch((err) => {
      el("state").textContent = String(err);
    });
  }
})();
