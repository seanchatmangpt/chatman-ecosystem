import unittest
from datetime import datetime,timezone
from scripts.measure_train.evidence_calibration.trial import CalibrationTrial
from scripts.measure_train.evidence_calibration.calibration import estimate
class T(unittest.TestCase):
 def test_estimator(self):
  now=datetime.now(timezone.utc)
  rows=[CalibrationTrial("s",str(i),True,i<4,now) for i in range(5)]
  e=estimate("s",rows)
  self.assertEqual(e.n,5); self.assertGreater(e.true_positive_rate,e.false_positive_rate)
