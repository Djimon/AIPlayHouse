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
