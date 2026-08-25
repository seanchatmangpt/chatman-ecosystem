import unittest
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.monotonicity import require_worst_loss_monotone
from scripts.measure_train.distributional_robustness_realization_msa.sensitivity import finite_difference
from scripts.measure_train.distributional_robustness_realization_msa.breakdown import empirical_breakdown_radius
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_radius_trajectory(self):
  pts=[(Fraction(0),Fraction(1,10)),(Fraction(1,10),Fraction(2,10)),(Fraction(2,10),Fraction(5,10))]
  self.assertTrue(require_worst_loss_monotone(pts)); self.assertEqual(finite_difference(pts).max_slope,Fraction(3)); self.assertEqual(empirical_breakdown_radius(pts,Fraction(3,10)),Fraction(2,10))
  with self.assertRaisesRegex(Refused,"NON_MONOTONE"): require_worst_loss_monotone([(Fraction(0),Fraction(2,10)),(Fraction(1,10),Fraction(1,10))])
