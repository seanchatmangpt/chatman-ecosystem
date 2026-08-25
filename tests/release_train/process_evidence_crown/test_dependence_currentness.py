import unittest
from fractions import Fraction
from scripts.release_train.process_evidence_crown import *
from scripts.release_train.process_evidence_crown.currentness import current_frontier
class T(unittest.TestCase):
 def setUp(self): self.s=Subject.parse('a/b','a'*40,'b'*64)
 def node(self,i,impl,model,domain): return EvidenceNode(i,self.s,EvidenceKind.ORACLE,2,Interval(Fraction(4,5),Fraction(9,10)),Outcome.PASS,impl,model,domain)
 def test_unknown_dependence_is_conservative(self):
  a=self.node('a','i1','m1','d1'); b=self.node('b','i2','m2','d2'); c=compose([a,b]); self.assertFalse(c.independent); self.assertEqual(c.interval.lo,Fraction(3,5))
 def test_independence_requires_witness(self):
  a=self.node('a','i1','m1','d1'); b=self.node('b','i2','m2','d2'); w=ProvenanceWitness('a','b',True,True,True); c=compose([a,b],[w]); self.assertTrue(c.independent); self.assertEqual(c.interval.lo,Fraction(16,25))
 def test_divergent_current_frontier_refuses(self):
  a=self.node('a','i1','m1','d'); b=self.node('b','i2','m2','d')
  with self.assertRaises(Refused): current_frontier([a,b])
