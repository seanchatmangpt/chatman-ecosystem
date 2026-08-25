import unittest
from scripts.release_train.calibrated_composition_crown import *
from scripts.release_train.calibrated_composition_crown.sensitivity import Sensitivity
class T(unittest.TestCase):
 def world(self,state="PARTIAL_ALIVE"):
  s=Subject.parse("seanchatmangpt/chatman-ecosystem","a"*40,"b"*64)
  ca=Calibration("CONSERVATIVE",7,"c"*64,20,.95,.05,.5)
  cb=Calibration("INDEPENDENT",7,"d"*64,20,.90,.10,.2)
  sens={"CONSERVATIVE":Sensitivity(.1,.1),"INDEPENDENT":Sensitivity(.1,.1)}
  engines=[EngineWitness("BEAM","impl1","e"*64),EngineWitness("WASM","impl2","e"*64)]
  regions=[RegionEvidence("h1","r1",7,True,"f"*64),RegionEvidence("h2","r2",7,True,"1"*64)]
  rc=ReactorCorrespondence("b"*64,"2"*64,"e"*64,"b"*64)
  return qualify(s,[ca,cb],sens,Strategy.MAX_COVERAGE,METHODS,RAILS,FAILURES,engines,regions,rc,(state,),())
 def test_chicago_positive(self):
  q=self.world(); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertIsNotNone(q.receipt); self.assertEqual(replay(q.receipt,q.receipt.digest()),"REPLAY_MATCH")
 def test_red_suppresses_receipt(self):
  q=self.world("BUILD_BROKEN"); self.assertEqual(q.standing,"BUILD_BROKEN"); self.assertIsNone(q.receipt)
