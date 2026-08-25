import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *

class CorrespondenceFailure(unittest.TestCase):
    def test_engine_oracle_and_failures(self):
        engines=[EngineWitness("BEAM","beam","s","t","o"),EngineWitness("WASM","wasm","s","t","o")]
        self.assertTrue(require_engines(engines))
        oracles=[OracleWitness("p1","i1","m1","powl","d"),OracleWitness("p2","i2","m2","powl","d")]
        self.assertTrue(require_oracles(oracles,"powl"))
        self.assertEqual(len(require_complete(list(FailureWorld))),7)

    def test_engine_divergence_refuses(self):
        engines=[EngineWitness("A","a","s","t","o"),EngineWitness("B","b","s","X","o")]
        with self.assertRaises(Refused): require_engines(engines)

    def test_oracle_alias_refuses(self):
        oracles=[OracleWitness("p1","same","m1","powl","d"),OracleWitness("p2","same","m2","powl","d")]
        with self.assertRaises(Refused): require_oracles(oracles,"powl")

if __name__=="__main__": unittest.main()
