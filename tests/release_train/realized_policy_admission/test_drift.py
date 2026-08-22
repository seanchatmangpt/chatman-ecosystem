import unittest
from scripts.release_train.realized_policy_admission.drift import DriftState,page_hinkley
class T(unittest.TestCase):
    def test_shift(self):
        s=DriftState()
        for x in (0,0,0,1,1,1): s=page_hinkley(s,x,0.01,1.5)
        self.assertTrue(s.drifted)
