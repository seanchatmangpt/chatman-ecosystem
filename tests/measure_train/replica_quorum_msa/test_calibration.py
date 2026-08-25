import unittest
from scripts.measure_train.replica_quorum_msa.fault import FaultTrial
from scripts.measure_train.replica_quorum_msa.calibration import calibrate,CalibrationPolicy
class T(unittest.TestCase):
 def test_support_and_false_current_fence(self):
  good=[FaultTrial(str(i),"HEALTHY" if i%2==0 else "PARTITION","CURRENT" if i%2==0 else "NOT_CURRENT") for i in range(20)]
  self.assertEqual(calibrate(good,CalibrationPolicy(min_support=12,max_false_current_rate=.05,min_wilson_lower=.7))["state"],"CALIBRATED")
  self.assertEqual(calibrate(good[:3])["state"],"INSUFFICIENT")
