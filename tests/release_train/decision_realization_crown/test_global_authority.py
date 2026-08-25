import unittest
from scripts.release_train.decision_realization_crown import *
class T(unittest.TestCase):
  def test_global_correspondence_and_do_refusal(self):
    es=[EngineWitness("BEAM","a"*64,"b"*64,"c"*64,"d"*64),EngineWitness("WASM","e"*64,"f"*64,"c"*64,"d"*64)]; self.assertTrue(require_engines(es))
    os=[OracleWitness("POWL","1"*64,"2"*64,"r1"),OracleWitness("POWL","3"*64,"4"*64,"r2"),OracleWitness("OCEL","5"*64,"6"*64,"r3"),OracleWitness("OCEL","7"*64,"8"*64,"r4")]; self.assertTrue(require_oracles(os))
    rs=[RegionWitness("h1","us",True,"a"*64,True),RegionWitness("h2","eu",True,"b"*64,True)]; self.assertTrue(require_distribution(rs))
    with self.assertRaises(Refused): admit(ActionClass.DO)
