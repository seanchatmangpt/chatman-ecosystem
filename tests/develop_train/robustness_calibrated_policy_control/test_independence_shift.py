import unittest
from fractions import Fraction as F
from scripts.develop_train.robustness_calibrated_policy_control.independence import EvidenceIdentity,IndependenceProof
from scripts.develop_train.robustness_calibrated_policy_control.shift import total_variation
from scripts.develop_train.robustness_calibrated_policy_control.refusal import Refused
class T(unittest.TestCase):
 def test_independence_and_tv(self):
  a=EvidenceIdentity('IPS','i1','m1'); b=EvidenceIdentity('DR','i2','m2'); p=IndependenceProof(frozenset({frozenset((a,b))})); p.require((a,b))
  self.assertEqual(total_variation((F(3,4),F(1,4)),(F(1,2),F(1,2))),F(1,4))
  bad=EvidenceIdentity('SNIPS','i1','m3')
  with self.assertRaises(Refused): IndependenceProof(frozenset({frozenset((a,bad))})).require((a,bad))
