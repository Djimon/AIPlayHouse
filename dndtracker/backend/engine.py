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
    if action_type == "ADD_EFFECT":
        return _apply_add_effect(state=state, action=action)
    if action_type == "REMOVE_EFFECT":
        return _apply_remove_effect(state=state, action=action)
    if action_type == "APPLY_DAMAGE":
        return _apply_damage(state=state, action=action)
    if action_type == "RESOLVE_CONCENTRATION_SAVE":
        return _apply_resolve_concentration_save(state=state, action=action)
    if action_type == "APPLY_SAVE_RESULT":
        return _apply_save_result(state=state, action=action)
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


def _apply_add_effect(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    effects = list(next_state.get("effects", []))
    effect = action.get("effect")
    if isinstance(effect, dict):
        effects.append(dict(effect))
        next_state["effects"] = effects
        return ActionResult(
            state=next_state,
            engine_events=[{"kind": "effect_added", "effect": dict(effect), "action": action}],
        )
    return ActionResult(state=next_state, engine_events=[])


def _apply_remove_effect(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    effect_id = action.get("effectId")
    if not isinstance(effect_id, str) or effect_id == "":
        return ActionResult(state=next_state, engine_events=[])

    effects = list(next_state.get("effects", []))
    filtered = [effect for effect in effects if not (isinstance(effect, dict) and effect.get("id") == effect_id)]
    if len(filtered) == len(effects):
        return ActionResult(state=next_state, engine_events=[])

    next_state["effects"] = filtered
    return ActionResult(
        state=next_state,
        engine_events=[{"kind": "effect_removed", "effectId": effect_id, "action": action}],
    )


def _apply_damage(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    actor_id = action.get("actorId")
    damage_taken = int(action.get("damageTaken", 0))
    if not isinstance(actor_id, str) or actor_id == "" or damage_taken <= 0:
        return ActionResult(state=next_state, engine_events=[])

    concentration = dict(next_state.get("concentration", {}))
    current_entry = concentration.get(actor_id)
    if not current_entry:
        return ActionResult(state=next_state, engine_events=[])

    dc = max(10, damage_taken // 2)
    updated_entry: dict[str, Any]
    if isinstance(current_entry, dict):
        updated_entry = dict(current_entry)
    else:
        updated_entry = {}
    updated_entry["checkNeeded"] = True
    updated_entry["dc"] = dc
    updated_entry["lastDamageTaken"] = damage_taken
    concentration[actor_id] = updated_entry
    next_state["concentration"] = concentration
    return ActionResult(
        state=next_state,
        engine_events=[{"kind": "concentration_check_needed", "actorId": actor_id, "dc": dc, "action": action}],
    )


def _apply_resolve_concentration_save(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    actor_id = action.get("actorId")
    success = bool(action.get("success"))
    if not isinstance(actor_id, str) or actor_id == "":
        return ActionResult(state=next_state, engine_events=[])

    concentration = dict(next_state.get("concentration", {}))
    current_entry = concentration.get(actor_id)
    if current_entry is None:
        return ActionResult(state=next_state, engine_events=[])

    if success:
        updated_entry = dict(current_entry) if isinstance(current_entry, dict) else {}
        updated_entry["checkNeeded"] = False
        updated_entry["lastResult"] = "success"
        concentration[actor_id] = updated_entry
        next_state["concentration"] = concentration
        return ActionResult(
            state=next_state,
            engine_events=[{"kind": "concentration_resolved", "actorId": actor_id, "success": True, "action": action}],
        )

    concentration[actor_id] = None
    next_state["concentration"] = concentration
    effects = list(next_state.get("effects", []))
    filtered_effects = [
        effect
        for effect in effects
        if not (
            isinstance(effect, dict)
            and (
                effect.get("concentrationActorId") == actor_id
                or (effect.get("sourceActorId") == actor_id and effect.get("requiresConcentration") is True)
            )
        )
    ]
    next_state["effects"] = filtered_effects
    return ActionResult(
        state=next_state,
        engine_events=[{"kind": "concentration_resolved", "actorId": actor_id, "success": False, "action": action}],
    )


def _apply_save_result(state: dict[str, Any], action: dict[str, Any]) -> ActionResult:
    next_state = _with_running_status(state)
    effect_id = action.get("effectId")
    success = bool(action.get("success"))
    if not isinstance(effect_id, str) or effect_id == "":
        return ActionResult(state=next_state, engine_events=[])

    effects = list(next_state.get("effects", []))
    if not success:
        return ActionResult(
            state=next_state,
            engine_events=[{"kind": "save_applied", "effectId": effect_id, "success": False, "action": action}],
        )

    filtered = [effect for effect in effects if not (isinstance(effect, dict) and effect.get("id") == effect_id)]
    if len(filtered) != len(effects):
        next_state["effects"] = filtered
    return ActionResult(
        state=next_state,
        engine_events=[{"kind": "save_applied", "effectId": effect_id, "success": True, "action": action}],
    )


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
