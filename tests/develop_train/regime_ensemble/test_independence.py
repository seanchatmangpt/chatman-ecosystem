import unittest
from scripts.develop_train.regime_ensemble.detector_vote import DetectorVote
from scripts.develop_train.regime_ensemble.independence import IndependenceProof, independent_clique
class TestIndependence(unittest.TestCase):
    def test_same_family_or_unproven_edges_do_not_inflate_clique(self):
        vs=[DetectorVote("a","f","d1",True,1),DetectorVote("b","f","d2",True,1),DetectorVote("c","g","d3",True,1)]
        proofs=[IndependenceProof("a","b","x"),IndependenceProof("a","c","x")]
        self.assertEqual(tuple(v.name for v in independent_clique(vs,proofs)),("a","c"))
if __name__ == "__main__": unittest.main()
