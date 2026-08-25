import unittest
from fractions import Fraction
from scripts.release_train.process_evidence_crown import *
class T(unittest.TestCase):
 def test_exact_identity_and_dag(self):
  s=Subject.parse('seanchatmangpt/chatman-ecosystem','a'*40,'b'*64)
  n1=EvidenceNode('sem',s,EvidenceKind.SEMANTIC,1,Interval.point(1),Outcome.PASS,'i1','m1','d1')
  n2=EvidenceNode('trace',s,EvidenceKind.TRACE,1,Interval(Fraction(9,10),Fraction(1)),Outcome.PASS,'i2','m2','d2')
  g=EvidenceGraph({'sem':n1,'trace':n2},{'trace':('sem',)})
  self.assertEqual(g.order(),('sem','trace'))
 def test_cycle_refuses(self):
  s=Subject.parse('a/b','a'*40,'b'*64); n=EvidenceNode('x',s,EvidenceKind.SEMANTIC,1,Interval.point(1),Outcome.PASS,'i','m','d')
  with self.assertRaises(Refused): EvidenceGraph({'x':n},{'x':('x',)})
