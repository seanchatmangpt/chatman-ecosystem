import unittest
from scripts.release_train.calibrated_composition_crown import *
from scripts.release_train.calibrated_composition_crown.distributed import require_current_tls
from scripts.release_train.calibrated_composition_crown.engine import require_differential
class T(unittest.TestCase):
 def test_global(self):
  ws=[EngineWitness("BEAM","i1","t"*64),EngineWitness("WASM","i2","t"*64)]; self.assertTrue(require_differential(ws))
  rs=[RegionEvidence("h1","r1",1,True,"c"*64),RegionEvidence("h2","r2",1,True,"d"*64)]; self.assertTrue(require_current_tls(rs,1))
 def test_plaintext(self):
  with self.assertRaises(Refused): require_current_tls([RegionEvidence("h1","r1",1,False,"c"*64),RegionEvidence("h2","r2",1,True,"d"*64)],1)
