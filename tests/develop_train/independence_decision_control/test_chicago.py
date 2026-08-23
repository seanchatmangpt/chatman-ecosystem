import unittest
from fractions import Fraction as F

from scripts.develop_train.independence_decision_control import BetaEvidence, DecisionCalibration, LossMatrix, Receipt, Strategy, Subject, decide, qualify, replay
from scripts.develop_train.independence_decision_control.failure import REQUIRED_FAILURES
from scripts.develop_train.independence_decision_control.methodologies import REQUIRED


class TestChicago(unittest.TestCase):
    def test_full_bounded_path_and_replay(self):
        subject = Subject.parse("o/r@" + "a" * 40 + "#" + "b" * 64)
        result = decide(BetaEvidence(30, 2), LossMatrix(F(10), F(2), F(1)))
        calibration = DecisionCalibration(7, "c" * 64, 64, F(1, 100), F(1, 20), F(1, 10))
        self.assertTrue(calibration.admitted())
        qualification = qualify(decision=result.decision.value, generation=7, calibrated=True, drift=False, methodologies=REQUIRED, failures=REQUIRED_FAILURES)
        self.assertEqual(qualification.standing, "PARTIAL_ALIVE")
        receipt = Receipt(subject.key, Strategy.MIN_EXPECTED_LOSS.value, result.decision.value, 7, qualification.standing, "r" * 64)
        self.assertEqual(replay(receipt, receipt.digest()), "REPLAY_MATCH")

    def test_build_broken_dominates(self):
        qualification = qualify(decision="DEFER", generation=1, calibrated=True, drift=False, methodologies=REQUIRED, failures=REQUIRED_FAILURES, dependency="BUILD_BROKEN")
        self.assertEqual(qualification.standing, "BUILD_BROKEN")


if __name__ == "__main__":
    unittest.main()
