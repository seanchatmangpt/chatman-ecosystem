import unittest
from scripts.measure_train.strategy_binding.dependency import propagate
class T(unittest.TestCase):
 def test_block(self):
  r=propagate(["c","p"],[("c","p")],{"c":"PARTIAL_ALIVE","p":"BUILD_BROKEN"})
  self.assertEqual(r["c"],"BLOCKED")
