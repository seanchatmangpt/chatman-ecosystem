import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.certificate_federation_observability import *
C=Certificate(7,"c"*64,"d"*64,"e"*64,"f"*64); NOW=datetime.now(timezone.utc); T1=Transport("gh-api","impl-a","model-a","domain-a")
def resolved(i): return Observation(f"o{i}",T1.transport_id,7,TransportState.RESOLVED,Relation.EXACT,"a"*40,"b"*64,C.digest,NOW-timedelta(seconds=1),10+i)
class T(unittest.TestCase):
 def test_recovery_and_corr(self):
  c=Observation("c","gh-api",7,TransportState.TIMEOUT,Relation.CENSORED,None,None,None,NOW-timedelta(seconds=2),100); self.assertEqual(classify_recovery(c,resolved(1)),Recovery.OBSERVABILITY_RECOVERED)
  self.assertTrue(require_engines([EngineWitness("BEAM","i1","s","t","o"),EngineWitness("WASM","i2","s","t","o")]))
  self.assertTrue(require_oracles([OracleWitness("p1","i1","m1","powl","x"),OracleWitness("p2","i2","m2","powl","x")],"powl"))
 def test_divergence(self):
  with self.assertRaises(Refused): require_engines([EngineWitness("A","i1","s","t","o"),EngineWitness("B","i2","s","x","o")])
