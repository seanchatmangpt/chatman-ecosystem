import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.subject import Subject,Refused
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.policy import StrategyPolicy
from scripts.measure_train.strategy_binding.frontier import canonical_frontier
from scripts.measure_train.strategy_binding.proof import SelectionProof
from scripts.measure_train.strategy_binding.qualify import qualify
from scripts.measure_train.strategy_binding.replay import replay
class T(unittest.TestCase):
 def test_selection_proof_invalidates_on_frontier_change(self):
  n=datetime.now(timezone.utc); c1=CutCandidate("c1",1,(("o/a",1),("o/b",1)),n); policy=StrategyPolicy("LATEST_COMPLETE")
  _,d=canonical_frontier([c1]); p=SelectionProof(Subject("consumer/r","f"*40),"c1",policy.digest,d,"proof")
  q=qualify(p,policy,[c1],["PASS"]); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  c2=CutCandidate("c2",2,(("o/a",2),("o/b",2)),n)
  with self.assertRaises(Refused): qualify(p,policy,[c1,c2],["PASS"])
  self.assertFalse(q["actuation_performed"])
