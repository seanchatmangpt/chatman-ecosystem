import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.process_intelligence_substrate import Engine, Projection, RegionWitness, correspondence, require_current_agreement
from scripts.develop_train.process_intelligence_substrate.errors import Refused

class ProjectionDistributedTest(unittest.TestCase):
    def test_multi_engine_and_multi_region_correspondence(self):
        digest = "b" * 64
        a = Projection(Engine.BEAM, digest, frozenset({"trace","receipt"}))
        b = Projection(Engine.WASM, digest, frozenset({"trace","receipt"}))
        self.assertEqual(correspondence(a, b), frozenset({"trace","receipt"}))
        now = datetime.now(timezone.utc)
        witnesses = (RegionWitness("us", digest, now), RegionWitness("eu", digest, now))
        self.assertEqual(require_current_agreement(witnesses, now, timedelta(minutes=5)), digest)
        with self.assertRaises(Refused):
            correspondence(a, Projection(Engine.NIF, "c" * 64, frozenset({"trace","receipt"})))

if __name__ == "__main__": unittest.main()
