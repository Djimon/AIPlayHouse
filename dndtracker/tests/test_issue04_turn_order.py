from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.store import InMemoryEncounterStore


class Issue04TurnOrderTests(unittest.TestCase):
    def test_player_registration_and_initiative_order(self):
        store = InMemoryEncounterStore(server_salt="salt")
        app = create_app(store=store)
        client = TestClient(app)

        created = client.post("/api/encounters", json={"name": "Init"}).json()
        encounter_id = created["encounter_id"]
        host_token = created["host_token"]
        player_token = created["player_token"]

        response = client.post(
            f"/api/encounters/{encounter_id}/players",
            json={"token": host_token, "name": "Host"},
        )
        self.assertEqual(response.status_code, 403)

        response = client.post(
            f"/api/encounters/{encounter_id}/players",
            json={"token": player_token, "name": "Alice"},
        )
        self.assertEqual(response.status_code, 200)
        response = client.post(
            f"/api/encounters/{encounter_id}/players",
            json={"token": player_token, "name": "Bob"},
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()["state"]
        players = state["players"]
        self.assertEqual(len(players), 2)

        alice_id = players[0]["id"]
        bob_id = players[1]["id"]

        response = client.post(
            f"/api/encounters/{encounter_id}/actions",
            json={"token": host_token, "action": {"type": "SET_INITIATIVE", "playerId": alice_id, "initiative": 10}},
        )
        self.assertEqual(response.status_code, 200)
        response = client.post(
            f"/api/encounters/{encounter_id}/actions",
            json={"token": host_token, "action": {"type": "SET_INITIATIVE", "playerId": bob_id, "initiative": 15}},
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()["state"]
        self.assertEqual(state["turnOrder"], [bob_id, alice_id])

        response = client.post(
            f"/api/encounters/{encounter_id}/actions",
            json={"token": host_token, "action": {"type": "SET_INITIATIVE", "playerId": alice_id, "initiative": 12}},
        )
        response = client.post(
            f"/api/encounters/{encounter_id}/actions",
            json={"token": host_token, "action": {"type": "SET_INITIATIVE", "playerId": bob_id, "initiative": 12}},
        )
        state = response.json()["state"]
        self.assertEqual(state["turnOrder"], [alice_id, bob_id])


if __name__ == "__main__":
    unittest.main()
