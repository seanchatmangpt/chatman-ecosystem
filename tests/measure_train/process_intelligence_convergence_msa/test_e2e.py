import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.qualify import qualify
from scripts.measure_train.process_intelligence_convergence_msa.replay import replay
class T(unittest.TestCase):
 def test_partial_repair_with_remaining_broad_ci_red_is_build_broken(self):
  now=datetime.now(timezone.utc)
  a=ClosureEpoch(Subject("seanchatmangpt/ex4pm","a"*40,1),now,(ObligationState("reactor","FAIL"),ObligationState("broad_ci","FAIL"),ObligationState("replay","UNKNOWN")))
  b=ClosureEpoch(Subject("seanchatmangpt/ex4pm","b"*40,2),now+timedelta(seconds=1),(ObligationState("reactor","PASS"),ObligationState("broad_ci","FAIL"),ObligationState("replay","PASS")))
  q=qualify([a,b],[("replay","reactor")],now+timedelta(seconds=2),100)
  self.assertEqual(q["convergence"].direction,"CONVERGING")
  self.assertEqual(q["standing"],"BUILD_BROKEN")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
