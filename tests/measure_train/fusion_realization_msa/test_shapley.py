import unittest
from scripts.measure_train.fusion_realization_msa.shapley import shapley_values
class T(unittest.TestCase):
 def test_additive_contributions(self):
  weights={"a":1.0,"b":2.0,"c":3.0}; f=lambda s:sum(weights[x] for x in s)
  self.assertEqual(dict(shapley_values(weights,f)),weights)
