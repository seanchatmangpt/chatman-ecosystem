import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.validation_independence_control import EngineWitness, OracleWitness, Refused, RegionWitness, require_distribution, require_engine_correspondence, require_oracles

class GlobalCorrespondenceCourt(unittest.TestCase):
    def test_engine_oracle_and_region_correspondence(self):
        triple=("a"*64,"b"*64,"c"*64)
        self.assertTrue(require_engine_correspondence((EngineWitness("BEAM","impl-beam",*triple),EngineWitness("WASM","impl-wasm",*triple))))
        oracles=(OracleWitness("POWL","impl-powl-a","model-a","d"*64),OracleWitness("POWL","impl-powl-b","model-b","d"*64),OracleWitness("OCEL","impl-ocel-a","model-a","e"*64),OracleWitness("OCEL","impl-ocel-b","model-b","e"*64))
        self.assertTrue(require_oracles(oracles,"POWL")); self.assertTrue(require_oracles(oracles,"OCEL"))
        now=datetime(2026,8,23,14,30,tzinfo=timezone.utc)
        regions=(RegionWitness("h1","us-west",8,"a"*64,now-timedelta(minutes=1),now+timedelta(minutes=5),True,"f"*64),RegionWitness("h2","eu-west",8,"a"*64,now-timedelta(minutes=1),now+timedelta(minutes=5),True,"1"*64))
        self.assertTrue(require_distribution(regions,now))

    def test_semantic_divergence_and_plaintext_refuse(self):
        with self.assertRaises(Refused): require_engine_correspondence((EngineWitness("BEAM","i1","a"*64,"b"*64,"c"*64),EngineWitness("WASM","i2","d"*64,"b"*64,"c"*64)))
        now=datetime(2026,8,23,14,30,tzinfo=timezone.utc)
        with self.assertRaises(Refused) as tls: require_distribution((RegionWitness("h1","r1",1,"a"*64,now-timedelta(seconds=1),now+timedelta(seconds=1),False,"f"*64),RegionWitness("h2","r2",1,"a"*64,now-timedelta(seconds=1),now+timedelta(seconds=1),True,"e"*64)),now)
        self.assertEqual(tls.exception.code,"TLS_EVIDENCE_INVALID")

if __name__ == "__main__": unittest.main()
