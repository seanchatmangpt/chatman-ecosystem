import unittest
from fractions import Fraction as F
from scripts.develop_train.robustness_calibrated_policy_control import *
from scripts.develop_train.robustness_calibrated_policy_control.receipt import replay
class T(unittest.TestCase):
 def test_end_to_end(self):
  s=Subject('seanchatmangpt/chatman-ecosystem@'+'1'*40); cal=BoundCalibration(7,'c'*64,12,F(9,10),F(1,5),F(2,5)); cf=CalibrationFrontier((cal,))
  e1=EvidenceIdentity('IPS','i1','m1'); e2=EvidenceIdentity('DR','i2','m2'); proof=IndependenceProof(frozenset({frozenset((e1,e2))}))
  a=PolicyBound(PolicyIdentity(7,'a'*64),Interval(F(4,5),F(9,10)),F(4),F(1),F(1),7,'c'*64,(e1,e2))
  b=PolicyBound(PolicyIdentity(7,'b'*64),Interval(F(1,5),F(2,5)),F(2),F(2),F(2),7,'c'*64,(e1,e2))
  h=CompatibilityHypergraph(frozenset())
  out=RobustCompositionEngine().evaluate(s,(a,b),cf,proof,h,Strategy.MAX_LOWER,F(0),F(0),1)
  self.assertEqual(out.standing,'PARTIAL_ALIVE'); self.assertIsNotNone(out.transition); self.assertTrue(replay(out.receipt,out.receipt.digest())); self.assertFalse(out.receipt.actuation_performed)
