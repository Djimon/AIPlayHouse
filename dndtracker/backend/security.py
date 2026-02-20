"""Security helpers for token handling in the backend."""

from __future__ import annotations

import hashlib
import secrets


TOKEN_BYTES = 24


def generate_token() -> str:
    """Generate a URL-safe token for encounter access."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str, server_salt: str) -> str:
    """Create deterministic token hash via sha256(token + server_salt)."""
    payload = f"{token}{server_salt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_token(raw_token: str, expected_hash: str, server_salt: str) -> bool:
    """Compare raw token against a stored hash."""
    return hash_token(raw_token, server_salt) == expected_hash
