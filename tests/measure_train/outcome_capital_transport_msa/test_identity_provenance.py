import unittest
from scripts.measure_train.outcome_capital_transport_msa.subject import Subject,Refused
from scripts.measure_train.outcome_capital_transport_msa.provenance import EvidenceNode,admit_graph,require_independent
class T(unittest.TestCase):
 def test_exact_and_shared_ancestry(self):
  Subject("o/r","a"*40,"b"*64)
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
  nodes=[EvidenceNode("root",(),"1"*64,"2"*64,"root-domain","root"),EvidenceNode("a",("root",),"3"*64,"4"*64,"a-domain","a"),EvidenceNode("b",("root",),"5"*64,"6"*64,"b-domain","b")]
  g=admit_graph(nodes)
  with self.assertRaisesRegex(Refused,"SHARED_EVIDENCE_ANCESTRY"): require_independent("a","b",g)
