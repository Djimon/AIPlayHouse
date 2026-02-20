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
