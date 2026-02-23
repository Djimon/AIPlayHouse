from __future__ import annotations

import unittest

from backend.engine import apply_host_action
from backend.state import build_initial_state


class Issue06EngineTests(unittest.TestCase):
    def test_add_effect_sets_concentration_when_flagged(self):
        state = build_initial_state(encounter_id="enc-1", name="Issue6")
        action = {
            "type": "ADD_EFFECT",
            "effect": {"id": "eff-1", "concentrationActorId": "actor-1"},
        }

        result = apply_host_action(state=state, action=action)

        concentration = result.state["concentration"]
        self.assertIn("actor-1", concentration)
        self.assertEqual(concentration["actor-1"]["checkNeeded"], False)

    def test_next_turn_ticks_round_end_effects(self):
        state = build_initial_state(encounter_id="enc-2", name="Issue6")
        state["turnOrder"] = ["a", "b"]
        state["turnIndex"] = 1
        state["round"] = 1
        state["effects"] = [{"id": "eff-1", "roundsRemaining": 1}]

        result = apply_host_action(state=state, action={"type": "NEXT_TURN"})

        self.assertEqual(result.state["round"], 2)
        self.assertEqual(result.state["effects"], [])

    def test_apply_damage_sets_concentration_check(self):
        state = build_initial_state(encounter_id="enc-3", name="Issue6")
        state["concentration"] = {"actor-1": {"checkNeeded": False}}

        result = apply_host_action(
            state=state,
            action={"type": "APPLY_DAMAGE", "actorId": "actor-1", "damageTaken": 15},
        )

        entry = result.state["concentration"]["actor-1"]
        self.assertTrue(entry["checkNeeded"])
        self.assertEqual(entry["dc"], 10)

    def test_concentration_fail_removes_effects(self):
        state = build_initial_state(encounter_id="enc-4", name="Issue6")
        state["effects"] = [{"id": "eff-2", "concentrationActorId": "actor-1"}]
        state["concentration"] = {"actor-1": {"checkNeeded": True}}

        result = apply_host_action(
            state=state,
            action={"type": "RESOLVE_CONCENTRATION_SAVE", "actorId": "actor-1", "success": False},
        )

        self.assertEqual(result.state["concentration"]["actor-1"], None)
        self.assertEqual(result.state["effects"], [])

    def test_save_result_success_removes_effect(self):
        state = build_initial_state(encounter_id="enc-5", name="Issue6")
        state["effects"] = [{"id": "eff-3"}, {"id": "eff-4"}]

        result = apply_host_action(
            state=state,
            action={"type": "APPLY_SAVE_RESULT", "effectId": "eff-3", "success": True},
        )

        self.assertEqual(result.state["effects"], [{"id": "eff-4"}])


if __name__ == "__main__":
    unittest.main()
