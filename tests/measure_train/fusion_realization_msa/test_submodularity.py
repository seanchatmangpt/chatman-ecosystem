import unittest
from scripts.measure_train.fusion_realization_msa.submodularity import submodularity_ratio
class T(unittest.TestCase):
 def test_ratio_is_bounded(self):
  f=lambda s:float(len(s))
  self.assertAlmostEqual(submodularity_ratio(("a","b"),f),1.0)
