from dndtracker.backend.state import build_initial_state


def test_build_initial_state_sets_v0_defaults() -> None:
    state = build_initial_state(encounter_id="enc-123", name="Goblin Cave")

    assert state["id"] == "enc-123"
    assert state["version"] == 1
    assert state["status"] == "setup"
    assert state["round"] == 1
    assert state["turnIndex"] == 0
    assert state["turnOrder"] == []
    assert state["actors"] == {}
    assert state["effects"] == []
    assert state["concentration"] == {}
    assert state["chat"] == []
    assert state["log"] == []
    assert state["meta"]["name"] == "Goblin Cave"


def test_build_initial_state_uses_shared_timestamp_for_meta_fields() -> None:
    state = build_initial_state(encounter_id="enc-456", name="Crypt")

    assert state["meta"]["createdAt"] == state["meta"]["updatedAt"]
    assert state["meta"]["createdAt"].endswith("+00:00")
