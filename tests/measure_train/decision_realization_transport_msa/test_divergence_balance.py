import unittest
from fractions import Fraction
from scripts.measure_train.decision_realization_transport_msa.divergence import total_variation,jensen_shannon
from scripts.measure_train.decision_realization_transport_msa.balance import stratum_balance
class T(unittest.TestCase):
 def test_shift(self):
  p={"a":Fraction(1)};q={"b":Fraction(1)}
  self.assertEqual(total_variation(p,q),1.0);self.assertGreater(jensen_shannon(p,q),0)
  self.assertEqual(stratum_balance(p,q)["max_gap"],1.0)
