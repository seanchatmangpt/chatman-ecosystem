import unittest
from fractions import Fraction
from fixture import *
from scripts.release_train.feedback_policy_admission.calibration import GainCalibration
from scripts.release_train.feedback_policy_admission.efficiency import Efficiency
from scripts.release_train.feedback_policy_admission.strategies import candidates,select
class T(unittest.TestCase):
 def test_noncollapse(self):
  c=GainCalibration(3,Fraction(0),Fraction(0))
  e=Efficiency(Fraction(1),Fraction(1),Fraction(1))
  xs=candidates(c,False,e,Fraction(0))
  self.assertEqual(len({x.strategy for x in xs}),5)
  self.assertEqual(select(xs).strategy,FeedbackStrategy.HOLD)
if __name__=="__main__": unittest.main()
