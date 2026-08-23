import unittest
from datetime import datetime,timezone
from scripts.measure_train.outcome_capital_transport_msa.correspondence import EngineWitness,RegionWitness,require_engines,require_regions
from scripts.measure_train.outcome_capital_transport_msa.failure_worlds import require_complete,REQUIRED
from scripts.measure_train.outcome_capital_transport_msa.subject import Refused
class T(unittest.TestCase):
 def test_engine_region_failure_closure(self):
  engines=[EngineWitness("BEAM","a"*64,"b"*64,"c"*64,"d"*64,"e"*64),EngineWitness("PLAN","f"*64,"1"*64,"c"*64,"d"*64,"e"*64)]
  self.assertTrue(require_engines(engines))
  now=datetime.now(timezone.utc)
  regions=[RegionWitness("h1","r1","c"*64,True,"a"*64,now),RegionWitness("h2","r2","c"*64,True,"b"*64,now)]
  self.assertTrue(require_regions(regions,now))
  self.assertEqual(set(require_complete(REQUIRED)),REQUIRED)
  with self.assertRaises(Refused): require_regions([regions[0]],now)
