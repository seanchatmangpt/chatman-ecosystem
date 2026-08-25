import unittest
from scripts.develop_train.process_evidence_correspondence import *

class TestMethodEngineOracle(unittest.TestCase):
    def test_methodology_and_engine_correspondence(self):
        self.assertTrue(require_methodologies(REQUIRED))
        with self.assertRaises(Refused):
            require_methodologies({"DISCOVERY"})
        witnesses=[EngineWitness("BEAM","impl-a","sem","trace","obl"),EngineWitness("WASM","impl-b","sem","trace","obl")]
        self.assertTrue(require_engine_correspondence(witnesses))
        divergent=[EngineWitness("BEAM","impl-a","sem","trace","obl"),EngineWitness("WASM","impl-b","sem","other","obl")]
        with self.assertRaises(Refused):
            require_engine_correspondence(divergent)

    def test_independent_powl_and_ocel_oracles(self):
        witnesses=[OracleWitness("POWL","p1","m1","sem","pv"),OracleWitness("POWL","p2","m2","sem","pv"),OracleWitness("OCEL","o1","n1","sem","ov"),OracleWitness("OCEL","o2","n2","sem","ov")]
        self.assertTrue(require_oracles(witnesses))

if __name__ == "__main__": unittest.main()
