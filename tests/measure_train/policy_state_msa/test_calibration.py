import unittest
from scripts.measure_train.policy_state_msa.fault_trial import FaultTrial
from scripts.measure_train.policy_state_msa.calibration import calibrate
class T(unittest.TestCase):
    def test_support_required(self):
        self.assertEqual(calibrate([FaultTrial("STALE_CAS",True,True,"x")]).state,"INSUFFICIENT")
