from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.selection_intent_runtime.policy import *
class TestPolicy(unittest.TestCase):
 def test_digest_order_and_duplicate_refusal(self):
  a=StrategyPolicy(CutStrategy.MAX_FRESHNESS,(("b","2"),("a","1"))); b=StrategyPolicy(CutStrategy.MAX_FRESHNESS,(("a","1"),("b","2"))); self.assertEqual(a.digest,b.digest)
  with self.assertRaisesRegex(ValueError,"DUPLICATE_POLICY_PARAMETER"): StrategyPolicy(CutStrategy.MAX_FRESHNESS,(("a","1"),("a","2")))
