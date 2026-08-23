import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.information import binary_entropy,expected_information_gain
class TestInformation(unittest.TestCase):
 def test_information_gain_is_operational(self):
  self.assertAlmostEqual(binary_entropy(Fraction(1,2)),1.0)
  gain=expected_information_gain(Fraction(1,2),Fraction(1,2),Fraction(1,10),Fraction(9,10)); self.assertGreater(gain,0.5)
