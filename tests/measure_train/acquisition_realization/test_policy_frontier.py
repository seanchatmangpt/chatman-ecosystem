import unittest
from scripts.measure_train.acquisition_realization.policy_frontier import PolicyCalibration,current_frontier
from scripts.measure_train.acquisition_realization.subject import Refused
class T(unittest.TestCase):
 def test_divergent_generation_refuses(self):
  a=PolicyCalibration("MAX_INFORMATION_GAIN",2,"CALIBRATED",10,0.1)
  b=PolicyCalibration("MAX_INFORMATION_GAIN",2,"UNRELIABLE",10,0.5)
  with self.assertRaises(Refused): current_frontier([a,b])
