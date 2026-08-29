import unittest
from scripts.release_train.compositional_robustness_admission import DependencyGraph, ActionClass, admit
from scripts.release_train.compositional_robustness_admission.refusal import Refused
class T(unittest.TestCase):
    def test_red_dependency_and_do_refusal(self):
        g=DependencyGraph({"root":("dep",)},{"dep":"BUILD_BROKEN"}); self.assertEqual(g.blockers("root"),("dep",))
        with self.assertRaises(Refused): admit(ActionClass.DO)
