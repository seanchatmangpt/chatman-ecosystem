import unittest
from scripts.release_train.outcome_capital_transport import *
from scripts.release_train.outcome_capital_transport.authority import ActionClass

class T(unittest.TestCase):
 def test_chicago_and_failure_dominance(self):
  s=Subject.parse("a/b","a"*40,"b"*64)
  require_engines([EngineWitness("beam","i1","m1","s","t","o"),EngineWitness("wasm","i2","m2","s","t","o")])
  require_regions([RegionWitness("h1","r1",True,"c1",1),RegionWitness("h2","r2",True,"c2",1)],1)
  dg=DependencyGraph({"root":("dep",)}, {"dep":"PARTIAL_ALIVE"})
  q=Qualification(s,1,REQUIRED_METHODOLOGIES,REQUIRED_FAILURES,dg,"root",{"support":1},{"tv":"0"})
  standing,receipt=q.qualify(); self.assertEqual(standing,"PARTIAL_ALIVE"); self.assertEqual(replay(receipt,receipt.digest()),"REPLAY_MATCH")
  with self.assertRaises(Refused): admit(ActionClass.DO)
  broken=DependencyGraph({"root":("dep",)}, {"dep":"BUILD_BROKEN"}); st,rc=Qualification(s,1,REQUIRED_METHODOLOGIES,REQUIRED_FAILURES,broken,"root",{},{}).qualify(); self.assertEqual(st,"BUILD_BROKEN"); self.assertIsNone(rc)
