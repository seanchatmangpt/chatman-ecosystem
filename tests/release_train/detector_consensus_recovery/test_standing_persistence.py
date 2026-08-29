import unittest
from scripts.release_train.detector_consensus_recovery.consensus import Consensus
from scripts.release_train.detector_consensus_recovery.standing import calculate
from scripts.release_train.detector_consensus_recovery.persistence import candidates,select
class Court(unittest.TestCase):
 def test_positive_ceiling(self): self.assertEqual(calculate(Consensus("STABLE_CONFIRMED",(),0,2),"STABLE"),"PARTIAL_ALIVE")
 def test_fail_dominates(self): self.assertEqual(calculate(Consensus("FAIL",(),0,0),"FAILED"),"BUILD_BROKEN")
 def test_all_stores_preserved(self): self.assertEqual([c.kind for c in candidates()],["MEMORY","JSONL","SQLITE"]); self.assertEqual(select(transactional_required=True).kind,"SQLITE")
