import unittest

from scripts.develop_train.calibrated_recovery_quorum.evidence_source import EvidenceSource
from scripts.develop_train.calibrated_recovery_quorum.independence import (
    IndependenceProof,
    Relation,
    correlated_clusters,
    relation,
)


class TestIndependence(unittest.TestCase):
    def test_family_correlation_and_explicit_independence(self):
        left = EvidenceSource("p1", "r1", "a1", "f")
        right = EvidenceSource("p2", "r2", "a2", "f")
        self.assertEqual(relation(left, right), Relation.CORRELATED)
        proof = IndependenceProof(left.fingerprint, right.fingerprint, "0" * 64)
        self.assertEqual(relation(left, right, (proof,)), Relation.INDEPENDENT)

    def test_cluster_closure(self):
        first = EvidenceSource("p1", "r1", "a1", "f")
        second = EvidenceSource("p2", "r2", "a2", "f")
        third = EvidenceSource("p3", "r3", "a3", "g")
        self.assertEqual(len(correlated_clusters((first, second, third))), 2)
