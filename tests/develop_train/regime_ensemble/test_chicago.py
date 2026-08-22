import unittest
from scripts.develop_train.regime_ensemble.budget import EvidenceBudget
from scripts.develop_train.regime_ensemble.engine import qualify
from scripts.develop_train.regime_ensemble.hysteresis import HysteresisState,RegimeState
from scripts.develop_train.regime_ensemble.independence import IndependenceProof
from scripts.develop_train.regime_ensemble.receipt import replay
from scripts.develop_train.regime_ensemble.sample import ErrorSample
from scripts.develop_train.regime_ensemble.standing import Standing
from scripts.develop_train.regime_ensemble.subject import Subject
from scripts.develop_train.regime_ensemble.window import SampleWindow
class TestChicago(unittest.TestCase):
    def test_regime_shift_requires_independent_consensus_and_hysteresis(self):
        subject=Subject("seanchatmangpt/chatman-ecosystem","d"*40)
        proofs=[IndependenceProof(a,b,"separate statistic and state") for a,b in [("cusum","ewma"),("cusum","page-hinkley"),("ewma","page-hinkley")]]
        budget=EvidenceBudget(100,3,100)
        stable=[ErrorSample(i,v,"observed") for i,v in enumerate([.1,.2,.1,.2,.1,.2])]
        q0=qualify(subject,stable,SampleWindow(0,6),proofs,HysteresisState(),Standing.PARTIAL_ALIVE,budget)
        self.assertEqual(q0.hysteresis.state,RegimeState.STABLE); self.assertTrue(replay(q0.receipt,q0.digest))
        shifted=[ErrorSample(i,v,"observed") for i,v in enumerate([.1,.1,.1,.95,.95,.95,.95,.95])]
        q1=qualify(subject,shifted,SampleWindow(0,8),proofs,q0.hysteresis,Standing.PARTIAL_ALIVE,budget)
        self.assertTrue(q1.consensus.changed); self.assertEqual(q1.hysteresis.state,RegimeState.SUSPECT); self.assertEqual(q1.standing,Standing.UNKNOWN)
        q2=qualify(subject,shifted,SampleWindow(0,8),proofs,q1.hysteresis,Standing.PARTIAL_ALIVE,budget)
        self.assertEqual(q2.hysteresis.state,RegimeState.DRIFT); self.assertEqual(q2.standing,Standing.UNKNOWN); self.assertTrue(replay(q2.receipt,q2.digest))
if __name__ == "__main__": unittest.main()
