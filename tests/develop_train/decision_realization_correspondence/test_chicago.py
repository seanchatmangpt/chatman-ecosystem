import unittest
from fractions import Fraction

from scripts.develop_train.decision_realization_correspondence import DecisionPolicy, LossMatrix, Observation, REQUIRED, Subject, qualify, replay


class ChicagoDecisionRealizationCourt(unittest.TestCase):
    def _observations(self):
        methods = sorted(REQUIRED)
        return [
            Observation(
                f"obs-{i}", 3, "INDEPENDENT", "INDEPENDENT", Fraction(), Fraction(1), Fraction(),
                method, "BEAM" if i % 2 == 0 else "WASM", "us" if i % 2 == 0 else "eu", f"root-{i}",
            )
            for i, method in enumerate(methods)
        ]

    def test_full_method_realization_is_bounded_and_replayable(self):
        subject = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        policy = DecisionPolicy("decision-v3", 3, "c" * 64, LossMatrix(Fraction(10), Fraction(2), Fraction(1)))
        result = qualify(subject, policy, self._observations())
        self.assertEqual(result.standing, "PARTIAL_ALIVE")
        self.assertIsNotNone(result.receipt)
        self.assertEqual(replay(result.receipt, result.receipt.digest()), "REPLAY_MATCH")

    def test_hard_dependency_dominates_and_suppresses_receipt(self):
        subject = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        policy = DecisionPolicy("decision-v3", 3, "c" * 64, LossMatrix(Fraction(10), Fraction(2), Fraction(1)))
        result = qualify(subject, policy, self._observations(), dependency_standings=("BUILD_BROKEN",))
        self.assertEqual(result.standing, "BUILD_BROKEN")
        self.assertIsNone(result.receipt)


if __name__ == "__main__":
    unittest.main()
