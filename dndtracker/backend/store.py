"""Persistence interfaces and implementations for encounter data."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from dndtracker.backend.models import CreatedEncounter, EncounterAccess, EncounterRecord
from dndtracker.backend.security import hash_token
from dndtracker.backend.state import build_initial_state


class EncounterStore(Protocol):
    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        """Create encounter and persist initial snapshot plus token hashes."""

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        """Return encounter state when token is valid."""

    def get_encounter_access(self, encounter_id: str, raw_token: str) -> EncounterAccess | None:
        """Return encounter role and state when token is valid."""


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
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None:
            return None
        return EncounterRecord(encounter_id=encounter_id, state=access.state)

    def get_encounter_access(self, encounter_id: str, raw_token: str) -> EncounterAccess | None:
        payload = self._encounters.get(encounter_id)
        if payload is None:
            return None

        raw_hash = hash_token(raw_token, self.server_salt)
        role: str | None = None
        for candidate_role, token_hash in payload["tokens"].items():
            if raw_hash == token_hash:
                role = candidate_role
                break

        if role is None:
            return None
        return EncounterAccess(encounter_id=encounter_id, role=role, state=payload["state"])


@dataclass
class PostgresEncounterStore:
    database_url: str
    server_salt: str

    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-02 scope")

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-02 scope")

    def get_encounter_access(self, encounter_id: str, raw_token: str) -> EncounterAccess | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-02 scope")


def create_store(database_url: str | None, server_salt: str) -> EncounterStore:
    if database_url:
        return PostgresEncounterStore(database_url=database_url, server_salt=server_salt)
    return InMemoryEncounterStore(server_salt=server_salt)
