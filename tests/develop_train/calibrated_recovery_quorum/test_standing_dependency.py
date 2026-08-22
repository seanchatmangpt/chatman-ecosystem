import unittest

from scripts.develop_train.calibrated_recovery_quorum.dependency import DependencyGraph
from scripts.develop_train.calibrated_recovery_quorum.standing import bounded_standing


class TestStandingDependency(unittest.TestCase):
    def test_ceiling_and_failure_dominance(self):
        self.assertEqual(
            bounded_standing(
                outcomes=("PASS", "PASS"),
                decision="ACCEPT_BOUNDED",
                independent_clusters=2,
                required_clusters=2,
                under_calibrated=False,
            ),
            "PARTIAL_ALIVE",
        )
        self.assertEqual(
            bounded_standing(
                outcomes=("PASS", "FAIL"),
                decision="ACCEPT_BOUNDED",
                independent_clusters=2,
                required_clusters=2,
                under_calibrated=False,
            ),
            "BUILD_BROKEN",
        )

    def test_blocker_propagation_and_cycle(self):
        graph = DependencyGraph((("root", "a"), ("a", "b")))
        self.assertEqual(graph.blockers("root", {"b": "BUILD_BROKEN"}), ("b",))
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_CYCLE"):
            DependencyGraph((("a", "b"), ("b", "a")))
