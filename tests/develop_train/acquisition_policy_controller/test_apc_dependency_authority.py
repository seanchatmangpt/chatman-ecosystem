from scripts.develop_train.acquisition_policy_controller.subject import Refusal
from scripts.develop_train.acquisition_policy_controller.dependency import DependencyGraph
from scripts.develop_train.acquisition_policy_controller.authority import ActionClass,admit_action
import unittest
class T(unittest.TestCase):
    def test_blockers_and_do_refusal(self):
        g=DependencyGraph({"root":("x",)},{"x":"BUILD_BROKEN"}); self.assertEqual(g.blockers("root"),("x",))
        with self.assertRaises(Refusal): admit_action(ActionClass.DO)
