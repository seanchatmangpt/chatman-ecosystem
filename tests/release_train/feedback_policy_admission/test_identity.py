import unittest
from fixture import *
from scripts.release_train.feedback_policy_admission.errors import Refused
class T(unittest.TestCase):
 def test_subject_policy(self):
  self.assertEqual(subject().exact,"seanchatmangpt/chatman-ecosystem@"+"a"*40)
  with self.assertRaises(Refused): Subject("x","main")
  with self.assertRaises(Refused): PolicyIdentity("p",-1,"x",FeedbackStrategy.HOLD)
if __name__=="__main__": unittest.main()
