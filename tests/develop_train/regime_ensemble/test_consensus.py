import unittest
from scripts.develop_train.regime_ensemble.detector_vote import DetectorVote
from scripts.develop_train.regime_ensemble.independence import IndependenceProof
from scripts.develop_train.regime_ensemble.consensus import decide
class TestConsensus(unittest.TestCase):
    def test_independent_two_of_three_changes(self):
        vs=[DetectorVote("a","fa","da",True,1),DetectorVote("b","fb","db",True,1),DetectorVote("c","fc","dc",False,0)]
        ps=[IndependenceProof(a,b,"different algorithms") for a,b in [("a","b"),("a","c"),("b","c")]]
        self.assertTrue(decide(vs,ps,2).changed)
if __name__ == "__main__": unittest.main()
