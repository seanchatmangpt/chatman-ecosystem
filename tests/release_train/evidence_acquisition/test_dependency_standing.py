import unittest

from scripts.release_train.evidence_acquisition.dependency import DependencyGraph
from scripts.release_train.evidence_acquisition.standing import bounded_standing

class DependencyStandingCourt(unittest.TestCase):
    def test_transitive_blockers_and_cycle(self):
        graph = DependencyGraph((("seanchatmangpt/chatman-ecosystem", "seanchatmangpt/gymact"), ("seanchatmangpt/gymact", "seanchatmangpt/ggen")))
        blockers = graph.blockers("seanchatmangpt/chatman-ecosystem", {"seanchatmangpt/ggen": "BUILD_BROKEN"})
        self.assertEqual(blockers, ("seanchatmangpt/ggen",))
        self.assertEqual(bounded_standing(2, blockers), "BLOCKED")
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_CYCLE"):
            DependencyGraph((("a", "b"), ("b", "a")))

if __name__ == "__main__":
    unittest.main()
