import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from dndtracker.backend.api import create_app
from dndtracker.backend.store import InMemoryEncounterStore


def test_post_encounters_returns_id_and_tokens() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    client = TestClient(create_app(store=store))

    response = client.post("/api/encounters", json={"name": "Session 1"})

    assert response.status_code == 200
    data = response.json()
    assert data["encounter_id"]
    assert data["host_token"]
    assert data["player_token"]
    assert data["host_token"] != data["player_token"]


def test_get_encounter_returns_full_state_for_valid_token() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    app = create_app(store=store)
    client = TestClient(app)

    created = client.post("/api/encounters", json={"name": "Session 1"}).json()
    encounter_id = created["encounter_id"]
    token = created["player_token"]

    response = client.get(f"/api/encounters/{encounter_id}", params={"token": token})

    assert response.status_code == 200
    state = response.json()["state"]
    assert state["id"] == encounter_id
    assert state["meta"]["name"] == "Session 1"


def test_get_encounter_rejects_invalid_token() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    app = create_app(store=store)
    client = TestClient(app)

    created = client.post("/api/encounters", json={"name": "Session 1"}).json()
    encounter_id = created["encounter_id"]

    response = client.get(f"/api/encounters/{encounter_id}", params={"token": "invalid"})

    assert response.status_code == 404


def test_websocket_sends_initial_state_after_connect() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    app = create_app(store=store)
    client = TestClient(app)

    created = client.post("/api/encounters", json={"name": "Session WS"}).json()
    encounter_id = created["encounter_id"]
    token = created["player_token"]

    with client.websocket_connect(f"/ws/encounters/{encounter_id}?token={token}") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "state.full"
    assert message["state"]["id"] == encounter_id


def test_websocket_rejects_invalid_token() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    app = create_app(store=store)
    client = TestClient(app)

    created = client.post("/api/encounters", json={"name": "Session WS"}).json()
    encounter_id = created["encounter_id"]

    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/encounters/{encounter_id}?token=invalid"):
            pass


def test_websocket_broadcasts_full_state_to_all_clients() -> None:
    store = InMemoryEncounterStore(server_salt="test-salt")
    app = create_app(store=store)

    with TestClient(app) as client:
        created = client.post("/api/encounters", json={"name": "Session WS"}).json()
        encounter_id = created["encounter_id"]
        host_token = created["host_token"]
        player_token = created["player_token"]

        with client.websocket_connect(f"/ws/encounters/{encounter_id}?token={host_token}") as ws_host:
            with client.websocket_connect(f"/ws/encounters/{encounter_id}?token={player_token}") as ws_player:
                ws_host.receive_json()
                ws_player.receive_json()

                broadcast_state = {
                    "id": encounter_id,
                    "version": 2,
                    "status": "running",
                    "round": 1,
                    "turnIndex": 0,
                    "turnOrder": [],
                    "actors": {},
                    "effects": [],
                    "concentration": {},
                    "chat": [],
                    "log": [],
                    "meta": {"name": "Session WS", "createdAt": "t0", "updatedAt": "t1"},
                }

                client.portal.call(app.state.publish_state, encounter_id, broadcast_state)

                host_message = ws_host.receive_json()
                player_message = ws_player.receive_json()

    assert host_message["type"] == "state.full"
    assert player_message["type"] == "state.full"
    assert host_message["state"] == broadcast_state
    assert player_message["state"] == broadcast_state
