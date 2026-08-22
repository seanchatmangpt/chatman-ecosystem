import unittest
from scripts.develop_train.epoch_discharge.resilience import deterministic_retry
class T(unittest.TestCase):
 def test_seed_replay(self):
  self.assertEqual(deterministic_retry(7,.6,5),deterministic_retry(7,.6,5))
  with self.assertRaisesRegex(ValueError,"INVALID_FAILURE_PROBABILITY"): deterministic_retry(1,1.1,2)
