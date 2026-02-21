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
