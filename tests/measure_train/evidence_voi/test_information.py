import unittest
from fractions import Fraction
from datetime import datetime,timezone
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.calibration import SensorCalibration
from scripts.measure_train.evidence_voi.information import binary_entropy,expected_information_gain
class T(unittest.TestCase):
 def test_information_invariants(self):
  b=BeliefState(Fraction(1,2),0); now=datetime.now(timezone.utc)
  informative=SensorCalibration("a",1,10,Fraction(9,10),Fraction(1,10),now)
  useless=SensorCalibration("b",1,10,Fraction(1,2),Fraction(1,2),now)
  self.assertAlmostEqual(binary_entropy(Fraction(1,2)),1.0)
  self.assertGreater(expected_information_gain(b,informative),0)
  self.assertAlmostEqual(expected_information_gain(b,useless),0.0)
