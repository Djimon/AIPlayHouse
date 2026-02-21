from dndtracker.backend.store import InMemoryEncounterStore, PostgresEncounterStore, create_store


def test_create_store_returns_postgres_store_when_database_url_present() -> None:
    store = create_store(database_url="postgresql://local", server_salt="salt")

    assert isinstance(store, PostgresEncounterStore)


def test_create_store_returns_in_memory_store_when_database_url_missing() -> None:
    store = create_store(database_url=None, server_salt="salt")

    assert isinstance(store, InMemoryEncounterStore)
