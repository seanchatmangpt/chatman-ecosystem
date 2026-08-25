import unittest
from types import SimpleNamespace
from scripts.measure_train.acquisition_realization.standing import standing
class T(unittest.TestCase):
 def test_bounded_and_failure_dominant(self):
  cal=SimpleNamespace(calibration_state="CALIBRATED")
  self.assertEqual(standing(cal,[SimpleNamespace(outcome="PASS")]),"PARTIAL_ALIVE")
  self.assertEqual(standing(cal,[SimpleNamespace(outcome="FAIL")]),"BUILD_BROKEN")
  self.assertEqual(standing(cal,[SimpleNamespace(outcome="PASS")],["BUILD_BROKEN"]),"BLOCKED")
