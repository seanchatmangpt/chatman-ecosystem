import unittest
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.calibration import Calibration
from scripts.measure_train.counterfactual_evaluator_msa.frontier import CalibrationModel,current_frontier
from scripts.measure_train.counterfactual_evaluator_msa.currentness import require_current
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_divergence_stale(self):
  c=Calibration("ips",3,Fraction(0),Fraction(0),Fraction(0),"CALIBRATED")
  a=CalibrationModel("ips",1,"1"*64,c); b=CalibrationModel("ips",1,"2"*64,c)
  with self.assertRaises(Refused): current_frontier([a,b])
  newer=CalibrationModel("ips",2,"3"*64,c); f=current_frontier([a,newer])
  with self.assertRaises(Refused): require_current(a,f)
