import unittest
from scripts.measure_train.calibration_regime.standing import bounded_standing
class T(unittest.TestCase):
 def test_failure_and_dependency_dominance(self):
  self.assertEqual(bounded_standing(['PASS'],'STABLE'),'PARTIAL_ALIVE')
  self.assertEqual(bounded_standing(['PASS','FAIL'],'STABLE'),'BUILD_BROKEN')
  self.assertEqual(bounded_standing(['PASS'],'STABLE',['BUILD_BROKEN']),'BLOCKED')
  self.assertEqual(bounded_standing(['PASS'],'DRIFT'),'UNKNOWN')
