import unittest
from scripts.release_train.outcome_capital_transport import EvidenceGraph,EvidenceNode,Refused,Subject

class T(unittest.TestCase):
 def test_identity_and_ancestry(self):
  s=Subject.parse("a/b","a"*40,"b"*64); self.assertIn("a/b@",s.key)
  g=EvidenceGraph([EvidenceNode("r1","i1","m1","d1"),EvidenceNode("a","i2","m2","d2",("r1",)),EvidenceNode("r2","i3","m3","d3"),EvidenceNode("b","i4","m4","d4",("r2",))]); self.assertTrue(g.independent_roots("a","b"))
  with self.assertRaises(Refused): EvidenceGraph([EvidenceNode("x","i","m","d",("x",))])
