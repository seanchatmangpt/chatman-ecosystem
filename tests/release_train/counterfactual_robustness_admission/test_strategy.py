from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
POL=PolicyIdentity("p",7,"b"*64)
class T(unittest.TestCase):
 def test_pareto_and_strategies_distinct(self):
  a=Candidate(POL.digest,Interval(F(2,5),F(3,5)),F(2)); b=Candidate("c"*64,Interval(F(1,2),F(9,10)),F(4)); xs=(a,b)
  self.assertEqual(select(xs,RobustStrategy.HOLD,POL.digest),a); self.assertEqual(select(xs,RobustStrategy.MAX_LOWER,POL.digest),b); self.assertIn(select(xs,RobustStrategy.MIN_WIDTH,POL.digest),xs); self.assertEqual(select(xs,RobustStrategy.MAX_BREAKDOWN,POL.digest),b)
