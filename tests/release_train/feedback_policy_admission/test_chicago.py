import unittest
from fixture import *
from scripts.release_train.feedback_policy_admission.trajectory import Trajectory
from scripts.release_train.feedback_policy_admission.qualification import qualify
from scripts.release_train.feedback_policy_admission.receipt import replay
from scripts.release_train.feedback_policy_admission.dependency import DependencyGraph
class T(unittest.TestCase):
 def test_current_hold_and_blocker(self):
  p=policy(); t=Trajectory(steps())
  q=qualify(subject=subject(),policy=p,frontier=(p,),trajectory=t)
  self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(q.selected_strategy,"HOLD")
  self.assertTrue(replay(q.receipt)); self.assertFalse(q.receipt.body["actuation_performed"])
  g=DependencyGraph({subject().repo:("dep",)},{"dep":"BUILD_BROKEN"})
  q2=qualify(subject=subject(),policy=p,frontier=(p,),trajectory=t,dependencies=g)
  self.assertEqual(q2.standing,"BLOCKED")
if __name__=="__main__": unittest.main()
