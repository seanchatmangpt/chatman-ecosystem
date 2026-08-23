import unittest
from scripts.measure_train.process_intelligence_closure.standing import standing

class T(unittest.TestCase):
    def test_failure_dominates_and_positive_bounded(self):
        full={"rail_states":{"A":"PASS"},"obligations":()}
        corr={"divergent":(),"contradictory":()}
        self.assertEqual(standing(full,corr),"PARTIAL_ALIVE")
        failed={"rail_states":{"A":"PASS","B":"FAIL"},"obligations":()}
        self.assertEqual(standing(failed,corr),"BUILD_BROKEN")
