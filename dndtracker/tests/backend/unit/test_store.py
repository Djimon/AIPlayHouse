from dndtracker.backend.models import EncounterAccess
from dndtracker.backend.store import InMemoryEncounterStore, PostgresEncounterStore, create_store


def test_create_store_returns_postgres_store_when_database_url_present() -> None:
    store = create_store(database_url="postgresql://local", server_salt="salt")

    assert isinstance(store, PostgresEncounterStore)


def test_create_store_returns_in_memory_store_when_database_url_missing() -> None:
    store = create_store(database_url=None, server_salt="salt")

    assert isinstance(store, InMemoryEncounterStore)


def test_in_memory_store_returns_role_for_valid_token() -> None:
    store = InMemoryEncounterStore(server_salt="salt")
    created = store.create_encounter(name="Session", host_token="host-1", player_token="player-1")

    host_access = store.get_encounter_access(encounter_id=created.encounter_id, raw_token="host-1")
    player_access = store.get_encounter_access(encounter_id=created.encounter_id, raw_token="player-1")

    assert host_access is not None
    assert player_access is not None
    assert host_access.role == "HOST"
    assert player_access.role == "PLAYER"


def test_in_memory_store_only_allows_host_actions() -> None:
    store = InMemoryEncounterStore(server_salt="salt")
    created = store.create_encounter(name="Session", host_token="host-1", player_token="player-1")

    state_forbidden = store.apply_action(
        encounter_id=created.encounter_id,
        raw_token="player-1",
        action={"type": "NEXT_TURN"},
    )
    state_allowed = store.apply_action(
        encounter_id=created.encounter_id,
        raw_token="host-1",
        action={"type": "NEXT_TURN"},
    )

    assert state_forbidden is None
    assert state_allowed is not None
    assert state_allowed["status"] == "running"
    assert state_allowed["version"] == 2


def test_in_memory_store_accepts_roll_and_chat_for_player() -> None:
    store = InMemoryEncounterStore(server_salt="salt")
    created = store.create_encounter(name="Session", host_token="host-1", player_token="player-1")

    roll_state = store.append_roll(
        encounter_id=created.encounter_id,
        raw_token="player-1",
        roll={"kind": "d20", "value": 12},
    )
    chat_state = store.append_chat(
        encounter_id=created.encounter_id,
        raw_token="player-1",
        message="hello",
    )

    assert roll_state is not None
    assert chat_state is not None
    assert chat_state["version"] == 3
    assert chat_state["chat"][-1]["text"] == "hello"
    assert chat_state["log"][-2]["kind"] == "roll"
    assert chat_state["log"][-1]["kind"] == "chat"


class _FakeCursor:
    def __init__(self) -> None:
        self.commands: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.commands.append((sql, params))

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = _FakeCursor()
        self.committed = False

    def cursor(self) -> _FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _PostgresStoreWithFakeConnection(PostgresEncounterStore):
    def __init__(self) -> None:
        super().__init__(database_url="postgresql://local", server_salt="salt")
        self.fake_connection = _FakeConnection()

    def _connect(self) -> _FakeConnection:
        return self.fake_connection


def test_postgres_apply_action_persists_snapshot_and_updates_version() -> None:
    store = _PostgresStoreWithFakeConnection()
    state = {
        "id": "enc-1",
        "version": 1,
        "status": "setup",
        "round": 1,
        "turnIndex": 0,
        "turnOrder": ["a", "b"],
        "effects": [],
        "meta": {
            "name": "Session",
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
        },
        "chat": [],
        "log": [],
    }

    store.get_encounter_access = lambda encounter_id, raw_token: EncounterAccess(
        encounter_id="enc-1",
        role="HOST",
        state=state,
    )

    next_state = store.apply_action(encounter_id="enc-1", raw_token="host", action={"type": "NEXT_TURN"})

    assert next_state is not None
    assert next_state["version"] == 2
    assert next_state["status"] == "running"
    assert store.fake_connection.committed is True
    assert len(store.fake_connection.cursor_instance.commands) == 2
    assert "INSERT INTO encounter_snapshots" in store.fake_connection.cursor_instance.commands[0][0]
    assert "UPDATE encounters" in store.fake_connection.cursor_instance.commands[1][0]


def test_postgres_apply_action_rejects_non_host() -> None:
    store = _PostgresStoreWithFakeConnection()
    store.get_encounter_access = lambda encounter_id, raw_token: None

    next_state = store.apply_action(encounter_id="enc-1", raw_token="player", action={"type": "NEXT_TURN"})

    assert next_state is None
    assert store.fake_connection.committed is False
