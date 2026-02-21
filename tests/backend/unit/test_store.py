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
