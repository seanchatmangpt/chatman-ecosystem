from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
from scripts.release_train.counterfactual_robustness_admission.refusal import Refused
def cals(): return (Calibration("ips",2,"1"*64,10,F(1,10),"2"*64),Calibration("dr",2,"3"*64,10,F(1,12),"4"*64,"5"*64))
class T(unittest.TestCase):
 def test_current_frontier_and_divergence(self):
  cs=cals(); f=CalibrationFrontier(cs); self.assertEqual(len(f.current()),2); f.require(cs[0]); bad=Calibration("ips",2,"9"*64,10,F(1,10),"2"*64)
  with self.assertRaises(Refused): CalibrationFrontier(cs+(bad,)).current()
