import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.acquisition import AcquisitionCandidate
from scripts.develop_train.fused_acquisition.pareto import frontier
class TestPareto(unittest.TestCase):
 def test_strict_dominance_only(self):
  a=AcquisitionCandidate('a','s1',Fraction(3,4),Fraction(3,4),2,2); b=AcquisitionCandidate('b','s2',Fraction(1,2),Fraction(1,2),3,3); c=AcquisitionCandidate('c','s3',Fraction(9,10),Fraction(1,10),1,5)
  self.assertEqual(frontier([a,b,c]),('a','c'))
