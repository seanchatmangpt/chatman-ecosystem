import unittest
from scripts.release_train.promotion_intent_lease.strategy import StrategyBinding
from scripts.release_train.promotion_intent_lease.subject import Refusal
class T(unittest.TestCase):
 def test_strategy_fingerprint(self):
  a=StrategyBinding.from_name('MAX_FRESHNESS',(('b','2'),('a','1')))
  b=StrategyBinding.from_name('MAX_FRESHNESS',(('a','1'),('b','2')))
  self.assertEqual(a.fingerprint(),b.fingerprint())
  with self.assertRaisesRegex(Refusal,'UNKNOWN_SELECTION_STRATEGY'): StrategyBinding.from_name('LATEST')
