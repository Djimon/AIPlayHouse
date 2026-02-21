from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.models import EncounterAccess
from backend.state import build_initial_state
from backend.store import InMemoryEncounterStore, PostgresEncounterStore


class FakeCursor:
    def __init__(self, statements: list[tuple[str, tuple]]):
        self._statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, params: tuple):
        self._statements.append((sql.strip(), params))


class FakeConnection:
    def __init__(self, statements: list[tuple[str, tuple]]):
        self._statements = statements
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor(self._statements)

    def commit(self):
        self.committed = True


class TestPostgresStore(PostgresEncounterStore):
    def __init__(self, access: EncounterAccess | None):
        super().__init__(database_url="postgresql://unused", server_salt="salt")
        self._access = access
        self.statements: list[tuple[str, tuple]] = []
        self.conn = FakeConnection(self.statements)

    def get_encounter_access(self, encounter_id: str, raw_token: str):
        return self._access

    def _connect(self):
        return self.conn


class Issue05RollsChatTests(unittest.TestCase):
    def test_roll_and_chat_allowed_for_host_and_player(self):
        store = InMemoryEncounterStore(server_salt="salt")
        app = create_app(store=store)
        client = TestClient(app)

        created = client.post("/api/encounters", json={"name": "Issue5"}).json()
        encounter_id = created["encounter_id"]

        host_roll = client.post(
            f"/api/encounters/{encounter_id}/rolls",
            json={"token": created["host_token"], "roll": {"kind": "d20", "value": 17}},
        )
        player_roll = client.post(
            f"/api/encounters/{encounter_id}/rolls",
            json={"token": created["player_token"], "roll": {"kind": "d20", "value": 12}},
        )
        host_chat = client.post(
            f"/api/encounters/{encounter_id}/chat",
            json={"token": created["host_token"], "message": "Host says hi"},
        )
        player_chat = client.post(
            f"/api/encounters/{encounter_id}/chat",
            json={"token": created["player_token"], "message": "Player says hi"},
        )

        self.assertEqual(host_roll.status_code, 200)
        self.assertEqual(player_roll.status_code, 200)
        self.assertEqual(host_chat.status_code, 200)
        self.assertEqual(player_chat.status_code, 200)

        state = player_chat.json()["state"]
        self.assertEqual(state["version"], 5)
        self.assertEqual(len(state["chat"]), 2)
        self.assertEqual(state["chat"][-1]["text"], "Player says hi")
        self.assertEqual(state["chat"][-1]["whoLabel"], "Player")
        self.assertEqual(len(state["log"]), 4)
        self.assertEqual(state["log"][0]["kind"], "roll")

    def test_postgres_append_roll_persists_roll_and_snapshot(self):
        base_state = build_initial_state(encounter_id="enc-1", name="Issue5")
        access = EncounterAccess(encounter_id="enc-1", role="PLAYER", state=base_state)
        store = TestPostgresStore(access=access)

        state = store.append_roll(encounter_id="enc-1", raw_token="tok", roll={"kind": "d20", "value": 18})

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["log"][-1]["kind"], "roll")
        self.assertTrue(store.conn.committed)
        self.assertEqual(len(store.statements), 3)
        self.assertIn("INSERT INTO encounter_rolls", store.statements[0][0])
        self.assertIn("INSERT INTO encounter_snapshots", store.statements[1][0])
        self.assertIn("UPDATE encounters", store.statements[2][0])

    def test_postgres_append_chat_persists_chat_and_snapshot(self):
        base_state = build_initial_state(encounter_id="enc-2", name="Issue5")
        access = EncounterAccess(encounter_id="enc-2", role="HOST", state=base_state)
        store = TestPostgresStore(access=access)

        state = store.append_chat(encounter_id="enc-2", raw_token="tok", message="Ping")

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["chat"][-1]["text"], "Ping")
        self.assertEqual(state["chat"][-1]["whoLabel"], "Host")
        self.assertTrue(store.conn.committed)
        self.assertEqual(len(store.statements), 3)
        self.assertIn("INSERT INTO encounter_chat", store.statements[0][0])
        self.assertIn("INSERT INTO encounter_snapshots", store.statements[1][0])
        self.assertIn("UPDATE encounters", store.statements[2][0])


if __name__ == "__main__":
    unittest.main()
