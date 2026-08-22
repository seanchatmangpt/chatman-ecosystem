from scripts.develop_train.acquisition_policy_controller.drift import DriftState,page_hinkley
import unittest
class T(unittest.TestCase):
    def test_shift_detected(self):
        s=DriftState()
        for x in [0,0,0,0,1,1,1]: s=page_hinkley(s,x,threshold=.3)
        self.assertTrue(s.drifted)
