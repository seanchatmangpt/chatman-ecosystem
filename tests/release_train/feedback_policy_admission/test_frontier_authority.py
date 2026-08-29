import unittest
from fixture import *
from scripts.release_train.feedback_policy_admission.frontier import PolicyFrontier
from scripts.release_train.feedback_policy_admission.authority import admit_action,ActionClass
from scripts.release_train.feedback_policy_admission.errors import Refused
class T(unittest.TestCase):
 def test_frontier_and_do(self):
  p=policy(); self.assertEqual(PolicyFrontier((p,)).current(),p)
  p2=policy(d="c"*64)
  with self.assertRaises(Refused): PolicyFrontier((p,p2)).current()
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
if __name__=="__main__": unittest.main()
