import unittest
from scripts.release_train.counterfactual_robustness_admission import manufacture,replay
from scripts.release_train.counterfactual_robustness_admission.receipt import Receipt
class T(unittest.TestCase):
 def test_replay_tamper(self):
  r=manufacture({"schema":"x","actuation_performed":False}); self.assertTrue(replay(r)); self.assertFalse(replay(Receipt({"schema":"y","actuation_performed":False},r.digest)))
