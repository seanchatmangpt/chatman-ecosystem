import unittest
from scripts.release_train.compositional_robustness_admission import EvidenceIdentity, IndependenceProof
from scripts.release_train.compositional_robustness_admission.refusal import Refused
class T(unittest.TestCase):
    def test_independence_is_explicit(self):
        a=EvidenceIdentity("a","1"*64,"2"*64); b=EvidenceIdentity("b","3"*64,"4"*64)
        self.assertTrue(IndependenceProof(frozenset({("a","b")})).require(a,b))
        with self.assertRaises(Refused): IndependenceProof(frozenset()).require(a,b)
