import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.frontier import canonical_frontier
class T(unittest.TestCase):
 def test_order_independent_digest(self):
  n=datetime.now(timezone.utc); a=CutCandidate("a",1,(("o/a",1),),n); b=CutCandidate("b",2,(("o/a",2),),n)
  self.assertEqual(canonical_frontier([a,b])[1],canonical_frontier([b,a])[1])
