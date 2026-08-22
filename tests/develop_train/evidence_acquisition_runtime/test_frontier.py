import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.calibration import SensorCalibration
from scripts.develop_train.evidence_acquisition_runtime.frontier import CalibrationFrontier
from scripts.develop_train.evidence_acquisition_runtime.subject import Refusal
class T(unittest.TestCase):
 def test_frontier_movement_invalidates_plan(self):
  n=datetime(2026,8,22,22,tzinfo=timezone.utc); c=lambda g: SensorCalibration('a',g,20,Fraction(9,10),Fraction(1,10),n)
  with self.assertRaisesRegex(Refusal,'STALE_CALIBRATION_FRONTIER'): CalibrationFrontier.build([c(1)]).assert_current(CalibrationFrontier.build([c(2)]))
