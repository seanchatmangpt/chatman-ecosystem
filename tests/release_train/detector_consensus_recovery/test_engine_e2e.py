import unittest
from scripts.release_train.detector_consensus_recovery.engine import qualify
from scripts.release_train.detector_consensus_recovery.receipt import replay
from scripts.release_train.detector_consensus_recovery.hysteresis import HysteresisState
from helpers import S,detector,generation,vote,proof
class Court(unittest.TestCase):
 def test_chicago_stable_then_drift(self):
  a=detector("cus","CUSUM","runner-a"); b=detector("ew","EWMA","runner-b"); ga,gb=generation(a),generation(b); p=[proof(a,b)]
  stable=qualify(subject=S,votes=[vote(a,ga,"STABLE"),vote(b,gb,"STABLE")],generations=[ga,gb],proofs=p,transactional=True)
  self.assertEqual(stable["standing"],"PARTIAL_ALIVE"); self.assertEqual(stable["store"].kind,"SQLITE"); self.assertTrue(replay(stable["receipt"]))
  drift1=qualify(subject=S,votes=[vote(a,ga,"DRIFT"),vote(b,gb,"DRIFT")],generations=[ga,gb],proofs=p,state=HysteresisState())
  self.assertEqual(drift1["state"].regime,"SUSPECT"); self.assertEqual(drift1["standing"],"UNKNOWN")
  drift2=qualify(subject=S,votes=[vote(a,ga,"DRIFT"),vote(b,gb,"DRIFT")],generations=[ga,gb],proofs=p,state=drift1["state"]); self.assertEqual(drift2["state"].regime,"DRIFT"); self.assertEqual(drift2["standing"],"PARTIAL_ALIVE")
 def test_dependency_failure_blocks(self):
  a=detector("cus","CUSUM","runner-a"); b=detector("ew","EWMA","runner-b"); ga,gb=generation(a),generation(b); dep="seanchatmangpt/dependency@"+"1"*40
  r=qualify(subject=S,votes=[vote(a,ga,"STABLE"),vote(b,gb,"STABLE")],generations=[ga,gb],proofs=[proof(a,b)],graph={S.identity:(dep,),dep:()},dependency_standing={dep:"BUILD_BROKEN"}); self.assertEqual(r["standing"],"BLOCKED")
