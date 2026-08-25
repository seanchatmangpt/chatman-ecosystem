import unittest
from scripts.measure_train.robustness_bound_msa.frontier import CalibrationModel,current_frontier
class T(unittest.TestCase):
 def test_latest_and_divergence(self):
  a=CalibrationModel("IPS",1,"a"*64,"CALIBRATED"); b=CalibrationModel("IPS",2,"b"*64,"CALIBRATED")
  self.assertEqual(current_frontier([a,b])[0],b)
