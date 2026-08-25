import unittest
from scripts.release_train.distributional_robustness_crown.api import *
class T(unittest.TestCase):
 def fixtures(self):
  s=Subject("seanchatmangpt/chatman-ecosystem","7"*40,"distributional",4); c=[Calibration(4,10,.2,.3,"cal")]; cases=[Realization(True,True,.05,0),Realization(False,False,.9,1)]; methods=REQUIRED; ds=("sem","trace","obl"); engines=[EngineWitness("BEAM","beam","m1",*ds),EngineWitness("WASM","wasm","m2",*ds)]; oracles=[OracleWitness("POWL","p","m1","p"),OracleWitness("OCEL","o","m2","o")]; regions=[RegionWitness("h1","r1",True,"c1",4),RegionWitness("h2","r2",True,"c2",4)]; return s,c,cases,methods,engines,oracles,regions
 def test_chicago_positive_is_bounded_and_replayable(self):
  s,c,cases,m,e,o,r=self.fixtures(); st,receipt=qualify(subject=s,calibrations=c,realizations=cases,methods=m,engines=e,oracles=o,regions=r,current_generation=4,worlds=list(World),dependency_graph={"root":()},dependency_standing={"root":"ALIVE"}); self.assertEqual(st,"PARTIAL_ALIVE"); self.assertEqual(replay(receipt),"REPLAY_MATCH")
 def test_build_broken_dominates(self):
  s,c,cases,m,e,o,r=self.fixtures(); st,receipt=qualify(subject=s,calibrations=c,realizations=cases,methods=m,engines=e,oracles=o,regions=r,current_generation=4,worlds=list(World),dependency_graph={"root":("bad",),"bad":()},dependency_standing={"bad":"BUILD_BROKEN"}); self.assertEqual((st,receipt),("BUILD_BROKEN",None))
