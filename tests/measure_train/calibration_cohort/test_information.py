import unittest
from fractions import Fraction
from types import SimpleNamespace
from scripts.measure_train.calibration_cohort.information import cohort_information
class T(unittest.TestCase):
 def test_balance_is_exact(self):
  s=SimpleNamespace(overlap=Fraction(3,4),common_micros=3)
  es=[SimpleNamespace(support=10),SimpleNamespace(support=30)]
  self.assertEqual(cohort_information(s,es)["support_balance"],Fraction(1,2))
