import unittest
from scripts.measure_train.fusion_realization_msa.calibration import calibrate_gain
from scripts.measure_train.fusion_realization_msa.cusum import two_sided_cusum
class T(unittest.TestCase):
 def test_support_and_drift(self):
  self.assertEqual(calibrate_gain(((.2,.2),)*4,min_support=5).status,"INSUFFICIENT")
  self.assertTrue(two_sided_cusum((.4,.4,.4),reference=.01,threshold=.5).drifted)
