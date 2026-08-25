import unittest
from fractions import Fraction
from scripts.measure_train.outcome_capital_transport_msa.population import Population
from scripts.measure_train.outcome_capital_transport_msa.shift import total_variation,js_divergence
from scripts.measure_train.outcome_capital_transport_msa.transport import weights
from scripts.measure_train.outcome_capital_transport_msa.subject import Refused
class T(unittest.TestCase):
 def test_shift_and_positivity(self):
  p=Population((("a",Fraction(1,2)),("b",Fraction(1,2))))
  q=Population((("a",Fraction(3,4)),("b",Fraction(1,4))))
  self.assertGreater(total_variation(p,q),0); self.assertGreater(js_divergence(p,q),0)
  self.assertEqual(weights(p,q)["a"],Fraction(3,2))
  bad=Population((("a",Fraction(1)),("b",Fraction(0))))
  with self.assertRaisesRegex(Refused,"POSITIVITY"): weights(bad,q)
