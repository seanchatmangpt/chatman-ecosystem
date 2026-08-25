import unittest
from scripts.measure_train.evidence_calibration.calibration import CalibrationEstimate
from scripts.measure_train.evidence_calibration.likelihood import contribution
class T(unittest.TestCase):
 def test_signal_direction(self):
  e=CalibrationEstimate("s",20,.9,.1,.1,.6)
  self.assertGreater(contribution(e,"PASS").log_lr,0)
  self.assertLess(contribution(e,"FAIL").log_lr,0)
