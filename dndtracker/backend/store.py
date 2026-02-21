"""Persistence interfaces and implementations for encounter data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Protocol
import uuid

from dndtracker.backend.engine import apply_host_action
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

        if event["kind"] == "action":
            reduced = apply_host_action(state=next_state, action=event["action"])
            next_state = reduced.state
            next_log.extend(reduced.engine_events)
            next_state["log"] = next_log

        return next_state


@dataclass
class PostgresEncounterStore:
    database_url: str
    server_salt: str

    def _connect(self) -> Any:
        import psycopg

        return psycopg.connect(self.database_url)

    def create_encounter(self, name: str, host_token: str, player_token: str) -> CreatedEncounter:
        encounter_id = str(uuid.uuid4())
        state = build_initial_state(encounter_id=encounter_id, name=name)
        now = datetime.now(timezone.utc)

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
                    VALUES (%s, %s, 'HOST', %s, %s, NULL), (%s, %s, 'PLAYER', %s, %s, NULL)
                    """,
                    (
                        str(uuid.uuid4()),
                        encounter_id,
                        hash_token(host_token, self.server_salt),
                        now,
                        str(uuid.uuid4()),
                        encounter_id,
                        hash_token(player_token, self.server_salt),
                        now,
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO encounter_snapshots (id, encounter_id, version, created_at, state_json)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (str(uuid.uuid4()), encounter_id, state["version"], now, json.dumps(state)),
                )
            conn.commit()

        return CreatedEncounter(encounter_id=encounter_id, host_token=host_token, player_token=player_token)

    def get_encounter_state(self, encounter_id: str, raw_token: str) -> EncounterRecord | None:
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None:
            return None
        return EncounterRecord(encounter_id=encounter_id, state=access.state)

    def get_encounter_access(self, encounter_id: str, raw_token: str) -> EncounterAccess | None:
        token_hash = hash_token(raw_token, self.server_salt)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.role, s.state_json
                    FROM encounters e
                    JOIN encounter_snapshots s
                      ON s.encounter_id = e.id AND s.version = e.current_version
                    JOIN encounter_tokens t
                      ON t.encounter_id = e.id
                    WHERE e.id = %s
                      AND t.token_hash = %s
                      AND t.revoked_at IS NULL
                    """,
                    (encounter_id, token_hash),
                )
                row = cur.fetchone()

        if row is None:
            return None

        role, state_json = row
        state = state_json if isinstance(state_json, dict) else json.loads(state_json)
        return EncounterAccess(encounter_id=encounter_id, role=role, state=state)

    def apply_action(self, encounter_id: str, raw_token: str, action: dict[str, Any]) -> dict[str, Any] | None:
        access = self.get_encounter_access(encounter_id=encounter_id, raw_token=raw_token)
        if access is None or access.role != "HOST":
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        event = {"kind": "action", "role": "HOST", "action": action}

        next_state = dict(access.state)
        next_state["version"] = int(access.state["version"]) + 1
        next_meta = dict(access.state["meta"])
        next_meta["updatedAt"] = now_iso
        next_state["meta"] = next_meta

        next_log = list(access.state.get("log", []))
        next_log.append(event)

        reduced = apply_host_action(state=next_state, action=action)
        next_state = reduced.state
        next_log.extend(reduced.engine_events)
        next_state["log"] = next_log

        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO encounter_snapshots (id, encounter_id, version, created_at, state_json)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (str(uuid.uuid4()), encounter_id, next_state["version"], now, json.dumps(next_state)),
                )
                cur.execute(
                    """
                    UPDATE encounters
                    SET current_version = %s, status = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (next_state["version"], next_state.get("status", "setup"), now, encounter_id),
                )
            conn.commit()

        return next_state

    def append_roll(self, encounter_id: str, raw_token: str, roll: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-05 scope")

    def append_chat(self, encounter_id: str, raw_token: str, message: str) -> dict[str, Any] | None:
        raise NotImplementedError("PostgresEncounterStore is not implemented in ISSUE-05 scope")


def create_store(database_url: str | None, server_salt: str) -> EncounterStore:
    if database_url:
        return PostgresEncounterStore(database_url=database_url, server_salt=server_salt)
    return InMemoryEncounterStore(server_salt=server_salt)
