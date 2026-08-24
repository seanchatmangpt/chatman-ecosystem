import unittest
from fractions import Fraction as F

from scripts.develop_train.independence_decision_control.drift import CUSUM
from scripts.develop_train.independence_decision_control.pareto import pareto
from scripts.develop_train.independence_decision_control.policy import Candidate, Strategy, select
from scripts.develop_train.independence_decision_control.voi import InformationOption


class TestDriftVoiPolicy(unittest.TestCase):
    def test_drift_and_positive_information_value(self):
        detector = CUSUM(F(1, 2))
        self.assertFalse(detector.update(F(1, 4)))
        self.assertTrue(detector.update(F(1, 3)))
        self.assertTrue(InformationOption(F(3), F(1), F(1)).worth_acquiring)

    def test_policies_do_not_collapse(self):
        candidates = (
            Candidate("safe", F(2), F(0), F(0), F(0), "DEPENDENT"),
            Candidate("learn", F(3), F(1, 10), F(5), F(0), "DEFER"),
        )
        self.assertNotEqual(select(candidates, Strategy.MIN_EXPECTED_LOSS), select(candidates, Strategy.MAX_INFORMATION_VALUE))
        self.assertEqual(len(pareto(candidates)), 2)


if __name__ == "__main__":
    unittest.main()
