import unittest
from scripts.measure_train.validation_independence_realization_msa.higher_order import higher_order_excess
class T(unittest.TestCase):
 def test_xor_exposes_higher_order(self):
  rows=[(0,0,0),(0,1,1),(1,0,1),(1,1,0)]*8
  self.assertGreater(higher_order_excess(rows),0.5)
