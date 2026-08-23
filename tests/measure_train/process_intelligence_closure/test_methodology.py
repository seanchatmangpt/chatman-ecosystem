import unittest
from scripts.measure_train.process_intelligence_closure.methodology import MethodologyCoverage,REQUIRED

class T(unittest.TestCase):
    def test_complete_and_missing(self):
        self.assertTrue(MethodologyCoverage(REQUIRED).complete)
        partial=MethodologyCoverage(REQUIRED-{"MONITORING"})
        self.assertEqual(partial.missing,("MONITORING",))
