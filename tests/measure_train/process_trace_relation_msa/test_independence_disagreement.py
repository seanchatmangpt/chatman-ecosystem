import unittest
from fractions import Fraction
from scripts.measure_train.process_trace_relation_msa.independence import OracleIndependence
from scripts.measure_train.process_trace_relation_msa.disagreement import disagreement_rate,binary_entropy
from scripts.measure_train.process_trace_relation_msa.subject import Refused
class T(unittest.TestCase):
 def test_independence_and_disagreement(self):
  self.assertTrue(OracleIndependence("a","b","m1","m2").require())
  with self.assertRaises(Refused): OracleIndependence("a","a","m1","m2").require()
  self.assertEqual(disagreement_rate({"x":1},{"x":2}),Fraction(1))
  self.assertEqual(binary_entropy(Fraction(1)),0.0)
