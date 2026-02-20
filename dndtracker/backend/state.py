"""State builders for encounter snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_initial_state(encounter_id: str, name: str) -> dict[str, Any]:
    """Return the V0 initial encounter state as defined in plan.md."""
    now = _utc_now_iso()
    return {
        "id": encounter_id,
        "version": 1,
        "status": "setup",
        "round": 1,
        "turnIndex": 0,
        "turnOrder": [],
        "actors": {},
        "effects": [],
        "concentration": {},
        "chat": [],
        "log": [],
        "meta": {
            "name": name,
            "createdAt": now,
            "updatedAt": now,
        },
    }
