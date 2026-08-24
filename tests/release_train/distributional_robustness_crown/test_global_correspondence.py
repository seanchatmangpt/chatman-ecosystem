import unittest
from scripts.release_train.distributional_robustness_crown.api import *
class T(unittest.TestCase):
 def test_global_contract(self):
  ds=("s","t","o"); es=[EngineWitness("BEAM","beam","m1",*ds),EngineWitness("WASM","wasm","m2",*ds)]; self.assertTrue(require_engines(es))
  os=[OracleWitness("POWL","powl","p1","x"),OracleWitness("OCEL","ocel","o1","y")]; self.assertTrue(require_oracles(os))
  rs=[RegionWitness("h1","r1",True,"c1",3),RegionWitness("h2","r2",True,"c2",3)]; self.assertTrue(require_regions(rs,3)); self.assertTrue(require_complete(list(World)))
