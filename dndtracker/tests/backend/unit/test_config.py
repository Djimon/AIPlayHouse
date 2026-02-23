from dndtracker.backend.config import load_settings


def test_load_settings_reads_expected_env(monkeypatch) -> None:
    monkeypatch.setenv("DNDTRACKER_SERVER_SALT", "salt-1")
    monkeypatch.setenv("DNDTRACKER_DATABASE_URL", "postgresql://local")
    monkeypatch.setenv("DNDTRACKER_HOST", "localhost")
    monkeypatch.setenv("DNDTRACKER_PORT", "9000")

    settings = load_settings()

    assert settings.server_salt == "salt-1"
    assert settings.database_url == "postgresql://local"
    assert settings.host == "localhost"
    assert settings.port == 9000


def test_load_settings_applies_defaults(monkeypatch) -> None:
    monkeypatch.delenv("DNDTRACKER_SERVER_SALT", raising=False)
    monkeypatch.delenv("DNDTRACKER_DATABASE_URL", raising=False)
    monkeypatch.delenv("DNDTRACKER_HOST", raising=False)
    monkeypatch.delenv("DNDTRACKER_PORT", raising=False)

    settings = load_settings()

    assert settings.server_salt == "dev-salt"
    assert settings.database_url is None
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
