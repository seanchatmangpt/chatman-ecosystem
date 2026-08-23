import unittest
from fractions import Fraction
from scripts.measure_train.decision_realization_transport_msa.weights import importance_weights
from scripts.measure_train.decision_realization_transport_msa.errors import Refused
class T(unittest.TestCase):
 def test_positivity(self):
  with self.assertRaises(Refused): importance_weights({"a":Fraction(1)},{"b":Fraction(1)})
  w=importance_weights({"a":Fraction(1)},{"a":Fraction(1)})
  self.assertEqual(w["a"],1)
