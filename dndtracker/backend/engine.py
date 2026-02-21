"""Reducer and engine helpers for host actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionResult:
    state: dict[str, Any]
    engine_events: list[dict[str, Any]]


def apply_host_action(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    """Apply a host action according to the V0 reducer baseline."""
    action_type = str(action.get("type", "")).upper()
    if action_type == "NEXT_TURN":
        return _apply_next_turn(state=state, action=action)
    return ActionResult(state=_with_running_status(state), engine_events=[])


def _with_running_status(state: dict[str, Any]) -> dict[str, Any]:
    next_state = dict(state)
    if state.get("status") == "setup":
        next_state["status"] = "running"
    return next_state


def _apply_next_turn(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    turn_order = list(next_state.get("turnOrder", []))
    if not turn_order:
        return ActionResult(
            state=next_state,
            engine_events=[{"kind": "timing", "timing": "turn_end", "actorId": None, "action": action}],
        )

    turn_index = int(next_state.get("turnIndex", 0))
    current_actor = turn_order[turn_index]

    events: list[dict[str, Any]] = [{"kind": "timing", "timing": "turn_end", "actorId": current_actor, "action": action}]

    new_turn_index = turn_index + 1
    wrapped = new_turn_index >= len(turn_order)
    if wrapped:
        new_turn_index = 0

    next_state["turnIndex"] = new_turn_index

    if wrapped:
        events.append({"kind": "timing", "timing": "round_end", "action": action})
        next_state["effects"] = _tick_round_end_effects(list(next_state.get("effects", [])))
        next_state["round"] = int(next_state.get("round", 1)) + 1
        events.append({"kind": "timing", "timing": "round_start", "action": action})

    new_actor = turn_order[new_turn_index]
    events.append({"kind": "timing", "timing": "turn_start", "actorId": new_actor, "action": action})

    return ActionResult(state=next_state, engine_events=events)


def _tick_round_end_effects(effects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    next_effects: list[dict[str, Any]] = []
    for effect in effects:
        if not isinstance(effect, dict):
            next_effects.append(effect)
            continue
        updated_effect = dict(effect)
        rounds_remaining = updated_effect.get("roundsRemaining")
        if isinstance(rounds_remaining, int):
            rounds_remaining -= 1
            if rounds_remaining <= 0:
                continue
            updated_effect["roundsRemaining"] = rounds_remaining
        next_effects.append(updated_effect)
    return next_effects
