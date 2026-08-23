import unittest
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission import AdmissionPolicy, Refused, admit_sensor
from common import model, frontier, visibility
class SensorQualityCourt(unittest.TestCase):
 def test_under_support_and_false_current_refuse(self):
  for m in (model(support=3),model(false_current_rate=Fraction(1,4))):
   with self.assertRaises(Refused): admit_sensor(m,frontier(m),visibility(),AdmissionPolicy())
 def test_visibility_and_lag_refuse(self):
  m=model()
  with self.assertRaises(Refused): admit_sensor(m,frontier(m),visibility(("r1",),lag=5),AdmissionPolicy())
  with self.assertRaises(Refused): admit_sensor(m,frontier(m),visibility(lag=999),AdmissionPolicy())
if __name__=="__main__": unittest.main()
