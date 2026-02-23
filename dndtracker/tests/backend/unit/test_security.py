from dndtracker.backend.security import generate_token, hash_token, verify_token


def test_hash_token_is_deterministic_for_same_inputs() -> None:
    token = "player-token"
    salt = "local-dev-salt"

    hashed_first = hash_token(token, salt)
    hashed_second = hash_token(token, salt)

    assert hashed_first == hashed_second
    assert len(hashed_first) == 64


def test_verify_token_accepts_valid_and_rejects_invalid_token() -> None:
    salt = "local-dev-salt"
    stored_hash = hash_token("host-token", salt)

    assert verify_token("host-token", stored_hash, salt) is True
    assert verify_token("wrong-token", stored_hash, salt) is False


def test_generate_token_returns_non_empty_random_value() -> None:
    first = generate_token()
    second = generate_token()

    assert first
    assert second
    assert first != second
