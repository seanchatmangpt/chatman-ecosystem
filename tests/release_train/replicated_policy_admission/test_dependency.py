import unittest
from fixtures import deps
from scripts.release_train.replicated_policy_admission.dependency import DependencyGraph
from scripts.release_train.replicated_policy_admission.refusal import Refused
class TestDependency(unittest.TestCase):
    def test_blocker(self): self.assertEqual(deps('BUILD_BROKEN').blockers(),('policy',))
    def test_cycle_refuses(self):
        with self.assertRaises(Refused): DependencyGraph((('a','b'),('b','a')),(('a','PARTIAL_ALIVE'),('b','PARTIAL_ALIVE'))).ordered()
