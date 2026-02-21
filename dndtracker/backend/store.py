"""Persistence interfaces and implementations for encounter data."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from dndtracker.backend.models import CreatedEncounter, EncounterRecord
from dndtracker.backend.security import hash_token
from dndtracker.backend.state import build_initial_state


class EncounterStore(Protocol):
    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        """Create encounter and persist initial snapshot plus token hashes."""

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        """Return encounter state when token is valid."""


@dataclass
class InMemoryEncounterStore:
    server_salt: str

    def __post_init__(self) -> None:
        self._encounters: dict[str, dict] = {}

    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        encounter_id = str(uuid.uuid4())
        state = build_initial_state(encounter_id=encounter_id, name=name)
        now = datetime.now(timezone.utc).isoformat()
        self._encounters[encounter_id] = {
            "state": state,
            "tokens": {
                "HOST": hash_token(host_token, self.server_salt),
                "PLAYER": hash_token(player_token, self.server_salt),
            },
            "createdAt": now,
            "updatedAt": now,
        }
        return CreatedEncounter(encounter_id=encounter_id, host_token=host_token, player_token=player_token)

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        payload = self._encounters.get(encounter_id)
        if payload is None:
            return None
        raw_hash = hash_token(raw_token, self.server_salt)
        valid = raw_hash in payload["tokens"].values()
        if not valid:
            return None
        return EncounterRecord(encounter_id=encounter_id, state=payload["state"])


@dataclass
class PostgresEncounterStore:
    database_url: str
    server_salt: str

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        encounter_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        state = build_initial_state(encounter_id=str(encounter_id), name=name)

        host_hash = hash_token(host_token, self.server_salt)
        player_hash = hash_token(player_token, self.server_salt)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO encounters (id, name, status, current_version, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (encounter_id, name, state["status"], state["version"], now, now),
                )
                cur.execute(
                    """
                    INSERT INTO encounter_tokens (id, encounter_id, role, token_hash, created_at, revoked_at)
                    VALUES (%s, %s, 'HOST', %s, %s, NULL),
                           (%s, %s, 'PLAYER', %s, %s, NULL)
                    """,
                    (uuid.uuid4(), encounter_id, host_hash, now, uuid.uuid4(), encounter_id, player_hash, now),
                )
                cur.execute(
                    """
                    INSERT INTO encounter_snapshots (id, encounter_id, version, created_at, state_json)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (uuid.uuid4(), encounter_id, state["version"], now, json.dumps(state)),
                )
            conn.commit()

        return CreatedEncounter(encounter_id=str(encounter_id), host_token=host_token, player_token=player_token)

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        raw_hash = hash_token(raw_token, self.server_salt)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.state_json
                    FROM encounter_snapshots s
                    JOIN encounters e ON e.id = s.encounter_id
                    WHERE s.encounter_id = %s
                      AND s.version = e.current_version
                      AND EXISTS (
                          SELECT 1
                          FROM encounter_tokens t
                          WHERE t.encounter_id = e.id
                            AND t.token_hash = %s
                            AND t.revoked_at IS NULL
                      )
                    """,
                    (encounter_id, raw_hash),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return EncounterRecord(encounter_id=encounter_id, state=row[0])


def create_store(*, database_url: str | None, server_salt: str) -> EncounterStore:
    if database_url:
        return PostgresEncounterStore(database_url=database_url, server_salt=server_salt)
    return InMemoryEncounterStore(server_salt=server_salt)
