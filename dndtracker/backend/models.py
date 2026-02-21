"""Domain models for encounter API responses and persistence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EncounterRecord:
    encounter_id: str
    state: dict[str, Any]


@dataclass(frozen=True)
class EncounterAccess:
    encounter_id: str
    role: str
    state: dict[str, Any]


@dataclass(frozen=True)
class EncounterTokens:
    host_token: str
    player_token: str


@dataclass(frozen=True)
class CreatedEncounter:
    encounter_id: str
    host_token: str
    player_token: str
