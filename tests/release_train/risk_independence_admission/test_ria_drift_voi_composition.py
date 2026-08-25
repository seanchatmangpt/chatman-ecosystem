import sys,unittest
from fractions import Fraction
sys.path.insert(0,'scripts/release_train')
from risk_independence_admission import *
from risk_independence_admission.drift import CusumState,advance,drifted
from risk_independence_admission.voi import value_of_information
from risk_independence_admission.composition import independent,conservative
from risk_independence_admission.decision import Decision
class DriftVOIComposition(unittest.TestCase):
 def test_drift_and_voi(self):
  s=CusumState()
  for _ in range(5): s=advance(s,Fraction(1,4),Fraction(1,20))
  self.assertTrue(drifted(s,1)); self.assertGreater(value_of_information(3,1,1),0)
 def test_modes_do_not_collapse(self):
  a,b=Interval('1/2','4/5'),Interval('1/2','9/10')
  self.assertNotEqual(independent(a,b),conservative(a,b))
  self.assertEqual(compose(a,b,Decision.INDEPENDENT),independent(a,b))
 def test_defer_refuses_narrowing(self):
  with self.assertRaises(Refused): compose(Interval(0,1),Interval(0,1),Decision.DEFER)
if __name__=='__main__':unittest.main()
