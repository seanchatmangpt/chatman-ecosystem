import unittest
from scripts.measure_train.calibration_cohort.subject import Subject,Refused
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
class T(unittest.TestCase):
 def test_identity_and_schema(self):
  s=Subject("o/r","a"*40); self.assertEqual(len(CalibrationSchema("truth","cusum","v1").fingerprint),64)
  with self.assertRaises(Refused): Subject("o/r","bad")
