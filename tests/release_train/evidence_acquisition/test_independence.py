import unittest

from scripts.release_train.evidence_acquisition.candidate import EvidenceCandidate
from scripts.release_train.evidence_acquisition.independence import IndependenceProof, admitted_independent

class IndependenceCourt(unittest.TestCase):
    def test_explicit_distinct_independence(self):
        left = EvidenceCandidate("a", "cusum", "runtime", "repo", 1, 1)
        right = EvidenceCandidate("b", "ewma", "workflow", "repo", 1, 1)
        self.assertFalse(admitted_independent(left, right, ()))
        self.assertTrue(admitted_independent(left, right, (IndependenceProof("a", "b"),)))
        correlated = EvidenceCandidate("c", "cusum", "workflow", "repo", 1, 1)
        self.assertFalse(admitted_independent(left, correlated, (IndependenceProof("a", "c"),)))

if __name__ == "__main__":
    unittest.main()
