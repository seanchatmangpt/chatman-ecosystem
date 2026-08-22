import unittest
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
from scripts.develop_train.evidence_acquisition_runtime.independence import IndependenceProof,admitted_pairs,pairwise_independent
class T(unittest.TestCase):
 def test_correlation_laundering_refused(self):
  C=lambda i,f,d: EvidenceCandidate(i,f,d,'s',Fraction(1),1); cs=[C('a','f','d1'),C('b','f','d2'),C('c','g','d3')]
  P=lambda a,b: IndependenceProof(a,b,'0'*64); pairs=admitted_pairs(cs,[P('a','b'),P('a','c')])
  self.assertNotIn(frozenset(('a','b')),pairs); self.assertIn(frozenset(('a','c')),pairs); self.assertFalse(pairwise_independent(['a','b'],pairs))
