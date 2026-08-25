import unittest
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.subject import Subject
from scripts.measure_train.robustness_bound_msa.calibration import BoundCalibration
from scripts.measure_train.robustness_bound_msa.frontier import CalibrationModel
from scripts.measure_train.robustness_bound_msa.qualify import qualify
from scripts.measure_train.robustness_bound_msa.replay import replay
class T(unittest.TestCase):
 def test_chicago(self):
  s=Subject("o/r","a"*40)
  c=BoundCalibration(10,Fraction(9,10),Fraction(1,3),Fraction(1,10),"CALIBRATED")
  m=CalibrationModel("ROBUST_IPS",3,"c"*64,"CALIBRATED")
  q=qualify(s,[c],[m])
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
