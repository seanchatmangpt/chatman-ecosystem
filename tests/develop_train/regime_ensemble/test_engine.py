import unittest
from scripts.develop_train.regime_ensemble.authority import ActionClass
from scripts.develop_train.regime_ensemble.budget import EvidenceBudget
from scripts.develop_train.regime_ensemble.engine import qualify
from scripts.develop_train.regime_ensemble.hysteresis import HysteresisState
from scripts.develop_train.regime_ensemble.independence import IndependenceProof
from scripts.develop_train.regime_ensemble.sample import ErrorSample
from scripts.develop_train.regime_ensemble.standing import Standing
from scripts.develop_train.regime_ensemble.subject import Subject
from scripts.develop_train.regime_ensemble.window import SampleWindow
class TestEngine(unittest.TestCase):
    def setUp(self):
        self.subject=Subject("o/r","c"*40); self.proofs=[IndependenceProof(a,b,"independent implementation") for a,b in [("cusum","ewma"),("cusum","page-hinkley"),("ewma","page-hinkley")]]
        self.budget=EvidenceBudget(100,3,100)
    def test_stable_series_is_bounded_partial_alive(self):
        xs=[ErrorSample(i,v,"obs") for i,v in enumerate([.1,.2,.1,.2,.1,.2])]
        q=qualify(self.subject,xs,SampleWindow(0,6),self.proofs,HysteresisState(),Standing.PARTIAL_ALIVE,self.budget)
        self.assertFalse(q.consensus.changed); self.assertEqual(q.standing,Standing.PARTIAL_ALIVE)
    def test_do_is_refused_before_qualification(self):
        xs=[ErrorSample(i,.1,"obs") for i in range(6)]
        with self.assertRaisesRegex(PermissionError,"BRCE"): qualify(self.subject,xs,SampleWindow(0,6),self.proofs,HysteresisState(),Standing.PARTIAL_ALIVE,self.budget,ActionClass.DO)
if __name__ == "__main__": unittest.main()
