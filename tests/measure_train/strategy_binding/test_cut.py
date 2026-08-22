import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.subject import Refused
class T(unittest.TestCase):
 def test_unique_producers(self):
  c=CutCandidate("c",1,(("o/a",1),),datetime.now(timezone.utc)); self.assertEqual(c.generation,1)
  with self.assertRaises(Refused): CutCandidate("x",1,(("o/a",1),("o/a",2)),datetime.now(timezone.utc))
