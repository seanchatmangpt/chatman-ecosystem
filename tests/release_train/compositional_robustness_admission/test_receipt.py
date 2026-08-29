import unittest
from dataclasses import replace
from scripts.release_train.compositional_robustness_admission import Receipt, replay
from scripts.release_train.compositional_robustness_admission.refusal import Refused
class T(unittest.TestCase):
    def test_replay_tamper_sensitive(self):
        r=Receipt("o/r@"+"a"*40,"HOLD",("b"*64,),"PARTIAL_ALIVE",())
        self.assertTrue(replay(r,r.digest))
        with self.assertRaises(Refused): replay(replace(r,standing="UNKNOWN"),r.digest)
