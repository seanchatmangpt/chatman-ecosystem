from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import Calibration
from scripts.release_train.counterfactual_robustness_admission.independence import require_independent
from scripts.release_train.counterfactual_robustness_admission.refusal import Refused
def cals(): return (Calibration("ips",2,"1"*64,10,F(1,10),"2"*64),Calibration("dr",2,"3"*64,10,F(1,12),"4"*64,"5"*64))
class T(unittest.TestCase):
 def test_explicit_independence(self):
  a,b=cals(); self.assertTrue(require_independent(a,b,{("ips","dr")}))
  with self.assertRaises(Refused): require_independent(a,b,set())
