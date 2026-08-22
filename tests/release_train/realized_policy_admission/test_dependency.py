import unittest
from scripts.release_train.realized_policy_admission.dependency import DependencyGraph
class T(unittest.TestCase):
    def test_transitive_blocker_and_cycle(self):
        g=DependencyGraph({"app":("lib",),"lib":("core",)},{"core":"BUILD_BROKEN"})
        self.assertEqual(g.blockers("app"),("core",))
        with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"): DependencyGraph({"a":("b",),"b":("a",)},{})
