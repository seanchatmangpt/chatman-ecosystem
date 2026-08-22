import unittest
from scripts.release_train.promotion_recovery.policy import StrategyPolicy
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_policy_is_deterministic_and_bounded(self):
  a=StrategyPolicy('MAX_FRESHNESS',(('b','2'),('a','1'))); b=StrategyPolicy('MAX_FRESHNESS',(('a','1'),('b','2')))
  self.assertEqual(a.digest,b.digest)
  with self.assertRaisesRegex(Refusal,'UNKNOWN_SELECTION_STRATEGY'): StrategyPolicy('MAGIC')
