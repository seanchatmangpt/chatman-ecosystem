import unittest
from datetime import datetime, timezone
from scripts.release_train.process_transition_crown import EngineWitness, RegionWitness, require_equivalent, require_current
from scripts.release_train.process_transition_crown.refusal import Refused

class EngineRegionTest(unittest.TestCase):
    def test_engine_divergence_refuses(self):
        a=EngineWitness("BEAM","s",("o",),"t")
        b=EngineWitness("WASM","x",("o",),"t")
        with self.assertRaises(Refused): require_equivalent((a,b))
    def test_region_independence_and_tls(self):
        now=datetime.now(timezone.utc)
        a=RegionWitness("h1","r1","s","27","c1",now,True)
        b=RegionWitness("h2","r2","s","27","c2",now,True)
        self.assertEqual(len(require_current((a,b),now,60)),2)

if __name__=="__main__": unittest.main()
