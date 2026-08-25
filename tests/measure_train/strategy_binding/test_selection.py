import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.policy import StrategyPolicy
from scripts.measure_train.strategy_binding.selection import select
class T(unittest.TestCase):
 def test_strategies_can_differ(self):
  n=datetime.now(timezone.utc)
  a=CutCandidate("latest",9,(("o/a",2),("o/b",2)),n)
  b=CutCandidate("fresh",8,(("o/a",8),("o/b",7)),n)
  self.assertEqual(select(StrategyPolicy("LATEST_COMPLETE"),[a,b]).cut_id,"latest")
  self.assertEqual(select(StrategyPolicy("MAX_FRESHNESS"),[a,b]).cut_id,"fresh")
