import unittest
from fractions import Fraction as F

from scripts.develop_train.independence_decision_control import BetaEvidence, Decision, LossMatrix, Refused, Subject, decide


class TestIdentityDecision(unittest.TestCase):
    def test_exact_identity_and_asymmetric_decision(self):
        Subject.parse("o/r@" + "a" * 40 + "#" + "b" * 64)
        result = decide(BetaEvidence(8, 2), LossMatrix(F(10), F(1), F(2)))
        self.assertIn(result.decision, {Decision.DEPENDENT, Decision.DEFER})

    def test_bad_subject_refuses(self):
        with self.assertRaises(Refused):
            Subject.parse("short")


if __name__ == "__main__":
    unittest.main()
