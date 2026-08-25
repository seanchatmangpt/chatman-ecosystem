import sys,unittest
from fractions import Fraction
sys.path.insert(0,'scripts/release_train')
from risk_independence_admission import *
from risk_independence_admission.dependence import higher_order_overlap,require_dependence_bounds
class AncestryCurrentness(unittest.TestCase):
 def test_disjoint_and_shared_ancestry(self):
  a=EvidenceAncestry((('a','r1'),('b','r2'))); self.assertTrue(a.require_disjoint('a','b'))
  bad=EvidenceAncestry((('a','root'),('b','root')))
  with self.assertRaises(Refused): bad.require_disjoint('a','b')
 def test_frontier_currentness(self):
  c=DecisionCalibration(2,'a'*64,20,'1/20','1/20','1/10'); f=CalibrationFrontier([c]); self.assertIs(f.require(2,'a'*64),c)
  with self.assertRaises(Refused): f.require(1,'a'*64)
 def test_higher_order_bound(self):
  h=higher_order_overlap(({1,2},{2,3},{2,4})); self.assertEqual(h,Fraction(1,4)); self.assertTrue(require_dependence_bounds(Fraction(1,10),h,Fraction(1,5),Fraction(1,3)))
if __name__=='__main__':unittest.main()
