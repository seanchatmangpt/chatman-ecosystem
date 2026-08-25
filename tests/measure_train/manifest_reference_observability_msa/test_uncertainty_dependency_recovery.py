import unittest
from fractions import Fraction
from scripts.measure_train.manifest_reference_observability_msa.uncertainty import identify
from scripts.measure_train.manifest_reference_observability_msa.dependency import dependency_graph,propagate
from scripts.measure_train.manifest_reference_observability_msa.recovery import classify

class T(unittest.TestCase):
 def test_partial_identification_and_recovery_classification(self):
  census=(("a",True,"EXACT",1),("b",True,"CENSORED",1),("c",True,"DIVERGED",1))
  b=identify(census)
  self.assertEqual(b.lower,Fraction(1,3)); self.assertEqual(b.upper,Fraction(2,3))
  g=dependency_graph(["a","b","c"],[("a","b")])
  self.assertEqual(propagate(census,g)["a"],"UNKNOWN")
  self.assertEqual(classify("CENSORED","EXACT"),"OBSERVABILITY_RECOVERED")
  self.assertEqual(classify("DIVERGED","EXACT"),"SEMANTIC_REPAIR")
