import unittest
from scripts.measure_train.trace_relation_selector_realization_msa.calibration import calibrate
from scripts.measure_train.trace_relation_selector_realization_msa.drift import cusum
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
from scripts.measure_train.trace_relation_selector_realization_msa.frontier import CalibrationFrontier,current_frontier
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Refused
class T(unittest.TestCase):
 def test_support_drift_and_divergence(self):
  self.assertEqual(calibrate([100000]*2,[False,False]).state,"INSUFFICIENT")
  self.assertTrue(cusum([0,1,1],0,1.5).alarm)
  a=CalibrationFrontier(SelectorIdentity(Selector.MINIMAX_ERROR,1,"a"*64),"b"*64,"CALIBRATED")
  b=CalibrationFrontier(SelectorIdentity(Selector.MINIMAX_ERROR,1,"a"*64),"c"*64,"CALIBRATED")
  with self.assertRaises(Refused): current_frontier([a,b])
