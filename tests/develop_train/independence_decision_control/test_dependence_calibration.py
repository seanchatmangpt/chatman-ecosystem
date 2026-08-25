import unittest
from fractions import Fraction as F

from scripts.develop_train.independence_decision_control.ancestry import EvidenceGraph, EvidenceNode
from scripts.develop_train.independence_decision_control.calibration import DecisionCalibration, current
from scripts.develop_train.independence_decision_control.dependence import DependenceEvidence
from scripts.develop_train.independence_decision_control.errors import Refused


class TestDependenceCalibration(unittest.TestCase):
    def test_shared_root_is_not_independent(self):
        graph = EvidenceGraph((EvidenceNode("r"), EvidenceNode("a", ("r",)), EvidenceNode("b", ("r",))))
        self.assertEqual(graph.overlap("a", "b"), frozenset({"r"}))
        self.assertFalse(DependenceEvidence(1, "d" * 64, F(1, 2), F(0), F(0)).independent)

    def test_split_current_refuses(self):
        left = DecisionCalibration(2, "a" * 64, 20, F(0), F(0), F(0))
        right = DecisionCalibration(2, "b" * 64, 20, F(0), F(0), F(0))
        with self.assertRaises(Refused):
            current((left, right))


if __name__ == "__main__":
    unittest.main()
