import unittest
from scripts.release_train.calibrated_recovery_quorum.calibration import CalibrationModel
from scripts.release_train.calibrated_recovery_quorum.likelihood import contribution
class T(unittest.TestCase):
 def test_zero_information(self):
  m=CalibrationModel("s",8,6,1,1,0)
  self.assertFalse(contribution(m,"UNKNOWN").informative); self.assertGreater(contribution(m,"PASS").value,0)
