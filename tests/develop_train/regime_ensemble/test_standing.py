import unittest
from scripts.develop_train.regime_ensemble.hysteresis import RegimeState
from scripts.develop_train.regime_ensemble.standing import Standing,bounded_standing
class TestStanding(unittest.TestCase):
    def test_failure_dominates_and_positive_ceiling_is_partial(self):
        self.assertEqual(bounded_standing(RegimeState.STABLE,Standing.BUILD_BROKEN,True),Standing.BUILD_BROKEN)
        self.assertEqual(bounded_standing(RegimeState.STABLE,Standing.PARTIAL_ALIVE,True),Standing.PARTIAL_ALIVE)
        self.assertEqual(bounded_standing(RegimeState.DRIFT,Standing.PARTIAL_ALIVE,True),Standing.UNKNOWN)
if __name__ == "__main__": unittest.main()
