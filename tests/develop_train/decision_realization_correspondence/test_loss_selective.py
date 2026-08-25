import unittest
from fractions import Fraction

from scripts.develop_train.decision_realization_correspondence import DecisionPolicy, LossMatrix, Observation, acted_coverage, defer_rate, selective_risk
from scripts.develop_train.decision_realization_correspondence.realized_loss import realized_loss


class LossSelectiveCourt(unittest.TestCase):
    def test_asymmetric_loss_and_abstention_are_distinct(self):
        policy = DecisionPolicy("p", 1, "c" * 64, LossMatrix(Fraction(10), Fraction(2), Fraction(1)))
        bad = Observation("bad", 1, "INDEPENDENT", "DEPENDENT", Fraction(1, 10), Fraction(1), Fraction(), "conformance", "BEAM", "us", "r1")
        defer = Observation("defer", 1, "DEFER", None, Fraction(1, 2), Fraction(1), Fraction(), "simulation", "PLAN", "eu", "r2")
        self.assertEqual(realized_loss(policy, bad), Fraction(10))
        self.assertEqual(acted_coverage([bad, defer]), Fraction(1, 2))
        self.assertEqual(defer_rate([bad, defer]), Fraction(1, 2))
        self.assertEqual(selective_risk(policy, [bad, defer]), Fraction(10))


if __name__ == "__main__":
    unittest.main()
