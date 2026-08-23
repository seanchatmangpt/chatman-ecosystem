import unittest
from fixture import *
from scripts.release_train.feedback_policy_admission.trajectory import Trajectory
from scripts.release_train.feedback_policy_admission.errors import Refused
class T(unittest.TestCase):
 def test_causal_trajectory(self):
  t=Trajectory(steps())
  self.assertEqual(t.total_predicted,Fraction(3,5))
  bad=list(steps()); bad[1]=StepRealization(2,"e1",1,1,1,1,1,bad[1].observed_at)
  with self.assertRaises(Refused): Trajectory(tuple(bad))
if __name__=="__main__": unittest.main()
