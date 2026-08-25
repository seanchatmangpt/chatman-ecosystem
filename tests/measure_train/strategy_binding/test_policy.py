import unittest
from scripts.measure_train.strategy_binding.policy import StrategyPolicy
from scripts.measure_train.strategy_binding.subject import Refused
class T(unittest.TestCase):
 def test_digest(self):
  a=StrategyPolicy("MAX_FRESHNESS",(("b","2"),("a","1"))); b=StrategyPolicy("MAX_FRESHNESS",(("a","1"),("b","2")))
  self.assertEqual(a.digest,b.digest)
  with self.assertRaises(Refused): StrategyPolicy("LATEST_WINS")
