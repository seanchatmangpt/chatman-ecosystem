import unittest
from scripts.measure_train.provenance.provenance import ProvenanceEdge
from scripts.measure_train.provenance.chain import validate_chain
from scripts.measure_train.provenance.subject import Refused
class T(unittest.TestCase):
 def test_cycle(self):
  es=[ProvenanceEdge("a","b","DERIVED_FROM"),ProvenanceEdge("b","a","DERIVED_FROM")]
  with self.assertRaises(Refused): validate_chain(["a","b"],es)
