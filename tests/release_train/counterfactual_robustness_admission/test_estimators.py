from datetime import datetime,timezone
from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
NOW=datetime(2026,8,23,5,35,tzinfo=timezone.utc)
def rows(): return admit_log([LoggedOutcome("e1",F(1,2),F(1,2),F(4,5),F(3,4),NOW),LoggedOutcome("e2",F(1,2),F(1,2),F(3,5),F(2,3),NOW),LoggedOutcome("e3",F(1,2),F(1,2),F(7,10),F(7,10),NOW)])
class T(unittest.TestCase):
 def test_estimators_and_support(self):
  r=rows(); self.assertEqual(ips(r),F(7,10)); self.assertEqual(snips(r),F(7,10)); self.assertTrue(F(0)<=doubly_robust(r)<=F(1)); p=profile(r); self.assertEqual(p.ess,F(3)); require_support(p)
