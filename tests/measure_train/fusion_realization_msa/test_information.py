import unittest
from scripts.measure_train.fusion_realization_msa.entropy import shannon_bits
from scripts.measure_train.fusion_realization_msa.js import js_divergence
from scripts.measure_train.fusion_realization_msa.ensemble import generalized_js
class T(unittest.TestCase):
 def test_information_geometry(self):
  self.assertAlmostEqual(shannon_bits((.5,.5)),1.0)
  self.assertAlmostEqual(js_divergence((.5,.5),(.5,.5)),0.0)
  self.assertGreater(generalized_js(((.9,.1),(.1,.9))),0)
