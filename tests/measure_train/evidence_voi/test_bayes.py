import unittest
from fractions import Fraction
from datetime import datetime,timezone
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.calibration import SensorCalibration
from scripts.measure_train.evidence_voi.predictive import predictive_distribution
from scripts.measure_train.evidence_voi.posterior import posterior
class T(unittest.TestCase):
 def test_normalization_and_direction(self):
  b=BeliefState(Fraction(1,2),0); c=SensorCalibration("a",1,10,Fraction(9,10),Fraction(1,10),datetime.now(timezone.utc))
  d=predictive_distribution(b,c); self.assertEqual(sum(d.values()),1)
  self.assertGreater(posterior(b,c,"PASS").p_alive,b.p_alive)
  self.assertLess(posterior(b,c,"FAIL").p_alive,b.p_alive)
