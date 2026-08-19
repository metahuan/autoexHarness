import unittest

from agent_harness import (
    ActionContract,
    ActionRequest,
    HarnessGate,
    PDCAMachine,
    Phase,
    StateTransitionError,
)


class HarnessGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = HarnessGate(
            [
                ActionContract(
                    action="publish",
                    required_fields=("target", "content"),
                    requires_evidence=True,
                )
            ]
        )

    def test_unknown_action_is_denied(self) -> None:
        result = self.gate.authorize(ActionRequest("delete_all", Phase.DO, {}))
        self.assertFalse(result.allowed)
        self.assertEqual(result.code, "unknown_action")

    def test_invalid_structure_and_missing_evidence_are_denied(self) -> None:
        result = self.gate.authorize(ActionRequest("publish", Phase.DO, {"target": "store"}))
        self.assertFalse(result.allowed)
        self.assertIn("missing required field: content", result.reasons)
        self.assertIn("evidence is required", result.reasons)

    def test_valid_request_is_allowed(self) -> None:
        result = self.gate.authorize(
            ActionRequest(
                "publish",
                Phase.DO,
                {"target": "store", "content": "approved copy"},
                ({"source": "review", "id": "review-1"},),
            )
        )
        self.assertTrue(result.allowed)
        self.assertTrue(result.receipt_id.startswith("rcpt_"))


class PDCAMachineTests(unittest.TestCase):
    def test_cannot_skip_check(self) -> None:
        machine = PDCAMachine(Phase.DO)
        with self.assertRaises(StateTransitionError):
            machine.advance(Phase.ACT, {"check_result": "pass"})

    def test_transition_requires_proof(self) -> None:
        machine = PDCAMachine()
        with self.assertRaises(StateTransitionError):
            machine.advance(Phase.DO, {})

    def test_full_cycle(self) -> None:
        machine = PDCAMachine()
        self.assertEqual(machine.advance(Phase.DO, {"plan_id": "p-1"}), Phase.DO)
        self.assertEqual(machine.advance(Phase.CHECK, {"execution_receipt": "r-1"}), Phase.CHECK)
        self.assertEqual(machine.advance(Phase.ACT, {"check_result": "pass"}), Phase.ACT)
        self.assertEqual(machine.advance(Phase.PLAN, {"retrospective": "improve"}), Phase.PLAN)


if __name__ == "__main__":
    unittest.main()
