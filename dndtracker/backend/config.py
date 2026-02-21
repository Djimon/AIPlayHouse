"""Configuration helpers for backend runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BackendSettings:
    server_salt: str
    database_url: str | None
    host: str
    port: int


def load_settings() -> BackendSettings:
    port_raw = os.getenv("DNDTRACKER_PORT", "8000")
    return BackendSettings(
        server_salt=os.getenv("DNDTRACKER_SERVER_SALT", "dev-salt"),
        database_url=os.getenv("DNDTRACKER_DATABASE_URL"),
        host=os.getenv("DNDTRACKER_HOST", "127.0.0.1"),
        port=int(port_raw),
    )
