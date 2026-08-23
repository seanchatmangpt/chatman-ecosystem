import unittest
from scripts.release_train.counterfactual_robustness_admission import *
from scripts.release_train.counterfactual_robustness_admission.refusal import Refused
SUB=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
class T(unittest.TestCase):
 def test_blockers_and_do_refusal(self):
  g=DependencyGraph({SUB.repo:("dep",),"dep":()}, {"dep":"BUILD_BROKEN"}); self.assertEqual(g.blockers(SUB.repo),("dep",))
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
