import unittest
from fractions import Fraction
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.dependence import IndependenceProof,independent
class T(unittest.TestCase):
 def test_unknown_or_shared_domain_not_independent(self):
  a=MeasurementCandidate("a","f1","d1","REPOSITORY",Fraction(1),1)
  b=MeasurementCandidate("b","f2","d1","REPOSITORY",Fraction(1),1)
  self.assertFalse(independent(b,[a],[IndependenceProof("a","b","separate code")]))
  c=MeasurementCandidate("c","f3","d3","REPOSITORY",Fraction(1),1)
  self.assertFalse(independent(c,[a],[]))
  self.assertTrue(independent(c,[a],[IndependenceProof("a","c","separate runtime")]))
