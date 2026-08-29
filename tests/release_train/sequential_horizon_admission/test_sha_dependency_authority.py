import unittest
from scripts.release_train.sequential_horizon_admission import ActionClass,Refused,admit_action
from scripts.release_train.sequential_horizon_admission.dependency import blockers
class T(unittest.TestCase):
 def test_transitive_red_and_direct_do_refuse(self):
  self.assertEqual(blockers({'release':['a'],'a':['b']},{'b':'BUILD_BROKEN'},'release'),('b',))
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
