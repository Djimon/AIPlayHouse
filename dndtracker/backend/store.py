"""Persistence interfaces and implementations for encounter data."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

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

    def apply_action(self, encounter_id: str, raw_token: str, action: dict[str, Any]) -> dict[str, Any] | None:
        """Apply a host action and return new state when authorized."""

    def append_roll(self, encounter_id: str, raw_token: str, roll: dict[str, Any]) -> dict[str, Any] | None:
        """Append a roll entry and return new state when authorized."""

    def append_chat(self, encounter_id: str, raw_token: str, message: str) -> dict[str, Any] | None:
        """Append a chat entry and return new state when authorized."""


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

    def apply_action(self, encounter_id: str, raw_token: str, action: dict[str, Any]) -> dict[str, Any] | None:
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None or access.role != "HOST":
            return None
        payload = self._encounters[encounter_id]
        payload["state"] = self._next_state_with_event(
            state=payload["state"],
            event={"kind": "action", "role": "HOST", "action": action},
        )
        return payload["state"]

    def append_roll(self, encounter_id: str, raw_token: str, roll: dict[str, Any]) -> dict[str, Any] | None:
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None:
            return None
        payload = self._encounters[encounter_id]
        payload["state"] = self._next_state_with_event(
            state=payload["state"],
            event={"kind": "roll", "role": access.role, "roll": roll},
        )
        return payload["state"]

    def append_chat(self, encounter_id: str, raw_token: str, message: str) -> dict[str, Any] | None:
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None:
            return None
        payload = self._encounters[encounter_id]
        payload["state"] = self._next_state_with_event(
            state=payload["state"],
            event={"kind": "chat", "role": access.role, "message": message},
        )
        return payload["state"]

    def _next_state_with_event(self, state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        next_state = dict(state)
        next_state["version"] = int(state["version"]) + 1
        next_meta = dict(state["meta"])
        next_meta["updatedAt"] = datetime.now(timezone.utc).isoformat()
        next_state["meta"] = next_meta

        next_log = list(state.get("log", []))
        next_log.append(event)
        next_state["log"] = next_log

        if event["kind"] == "chat":
            next_chat = list(state.get("chat", []))
            next_chat.append({"role": event["role"], "text": event["message"]})
            next_state["chat"] = next_chat

        if event["kind"] == "action" and state.get("status") == "setup":
            next_state["status"] = "running"

        return next_state


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

    def apply_action(self, encounter_id: str, raw_token: str, action: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-03 scope")

    def append_roll(self, encounter_id: str, raw_token: str, roll: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-03 scope")

    def append_chat(self, encounter_id: str, raw_token: str, message: str) -> dict[str, Any] | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-03 scope")


def create_store(database_url: str | None, server_salt: str) -> EncounterStore:
    if database_url:
        return PostgresEncounterStore(database_url=database_url, server_salt=server_salt)
    return InMemoryEncounterStore(server_salt=server_salt)
