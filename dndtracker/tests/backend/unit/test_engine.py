from dndtracker.backend.engine import apply_host_action


def test_apply_host_action_next_turn_advances_index_without_wrap() -> None:
    state = {
        "status": "setup",
        "round": 1,
        "turnIndex": 0,
        "turnOrder": ["a", "b", "c"],
        "effects": [],
    }

    result = apply_host_action(state=state, action={"type": "NEXT_TURN"})

    assert result.state["status"] == "running"
    assert result.state["turnIndex"] == 1
    assert result.state["round"] == 1
    assert [event["timing"] for event in result.engine_events] == ["turn_end", "turn_start"]


def test_apply_host_action_next_turn_wraps_round_and_ticks_effects() -> None:
    state = {
        "status": "running",
        "round": 2,
        "turnIndex": 1,
        "turnOrder": ["a", "b"],
        "effects": [
            {"id": "persist", "roundsRemaining": 2},
            {"id": "expire", "roundsRemaining": 1},
            {"id": "other"},
        ],
    }

    result = apply_host_action(state=state, action={"type": "NEXT_TURN"})

    assert result.state["turnIndex"] == 0
    assert result.state["round"] == 3
    assert result.state["effects"] == [
        {"id": "persist", "roundsRemaining": 1},
        {"id": "other"},
    ]
    assert [event["timing"] for event in result.engine_events] == [
        "turn_end",
        "round_end",
        "round_start",
        "turn_start",
    ]


def test_apply_host_action_add_and_remove_effect() -> None:
    state = {
        "status": "running",
        "effects": [{"id": "e1", "name": "Bless"}],
    }

    add_result = apply_host_action(
        state=state,
        action={"type": "ADD_EFFECT", "effect": {"id": "e2", "name": "Bane", "roundsRemaining": 2}},
    )

    assert [effect["id"] for effect in add_result.state["effects"]] == ["e1", "e2"]

    remove_result = apply_host_action(
        state=add_result.state,
        action={"type": "REMOVE_EFFECT", "effectId": "e1"},
    )

    assert remove_result.state["effects"] == [{"id": "e2", "name": "Bane", "roundsRemaining": 2}]


def test_apply_damage_sets_concentration_check_dc() -> None:
    state = {
        "status": "running",
        "concentration": {"caster": {"spell": "Hold Person", "checkNeeded": False}},
        "effects": [],
    }

    result = apply_host_action(
        state=state,
        action={"type": "APPLY_DAMAGE", "actorId": "caster", "damageTaken": 27},
    )

    entry = result.state["concentration"]["caster"]
    assert entry["checkNeeded"] is True
    assert entry["dc"] == 13
    assert result.engine_events[0]["kind"] == "concentration_check_needed"


def test_resolve_concentration_save_success_keeps_effects() -> None:
    state = {
        "status": "running",
        "concentration": {"caster": {"checkNeeded": True, "dc": 10}},
        "effects": [{"id": "e1", "concentrationActorId": "caster"}],
    }

    result = apply_host_action(
        state=state,
        action={"type": "RESOLVE_CONCENTRATION_SAVE", "actorId": "caster", "success": True},
    )

    assert result.state["concentration"]["caster"]["checkNeeded"] is False
    assert result.state["effects"] == [{"id": "e1", "concentrationActorId": "caster"}]


def test_resolve_concentration_save_failure_clears_concentration_and_effects() -> None:
    state = {
        "status": "running",
        "concentration": {"caster": {"checkNeeded": True, "dc": 10}},
        "effects": [
            {"id": "e1", "concentrationActorId": "caster"},
            {"id": "e2", "sourceActorId": "caster", "requiresConcentration": True},
            {"id": "e3", "concentrationActorId": "other"},
        ],
    }

    result = apply_host_action(
        state=state,
        action={"type": "RESOLVE_CONCENTRATION_SAVE", "actorId": "caster", "success": False},
    )

    assert result.state["concentration"]["caster"] is None
    assert [effect["id"] for effect in result.state["effects"]] == ["e3"]


def test_apply_save_result_success_removes_effect() -> None:
    state = {
        "status": "running",
        "effects": [
            {"id": "e-save", "saveEnds": True},
            {"id": "e-keep", "saveEnds": True},
        ],
    }

    result = apply_host_action(
        state=state,
        action={"type": "APPLY_SAVE_RESULT", "effectId": "e-save", "success": True},
    )

    assert [effect["id"] for effect in result.state["effects"]] == ["e-keep"]


def test_apply_save_result_failure_keeps_effect() -> None:
    state = {
        "status": "running",
        "effects": [{"id": "e-save", "saveEnds": True}],
    }

    result = apply_host_action(
        state=state,
        action={"type": "APPLY_SAVE_RESULT", "effectId": "e-save", "success": False},
    )

    assert [effect["id"] for effect in result.state["effects"]] == ["e-save"]
