import unittest
from scripts.release_train.recovery_evidence_quorum.dependency import DependencyGraph
class T(unittest.TestCase):
 def test_blocker(self): self.assertEqual(DependencyGraph([("a","b")]).blockers({"b":"BUILD_BROKEN"}),("b",))
 def test_cycle(self):
  with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"): DependencyGraph([("a","b"),("b","a")])
