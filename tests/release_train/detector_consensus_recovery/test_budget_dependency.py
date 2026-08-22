import unittest
from scripts.release_train.detector_consensus_recovery.budget import EvidenceBudget
from scripts.release_train.detector_consensus_recovery.dependencies import topological_order,blockers
class Court(unittest.TestCase):
 def test_budget_fails_closed(self):
  with self.assertRaisesRegex(ValueError,"EVIDENCE_BUDGET_EXCEEDED"): EvidenceBudget(max_detectors=2).admit(detectors=3,observations=1,proofs=1)
 def test_cycle_refused(self):
  with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"): topological_order({"a":("b",),"b":("a",)})
 def test_red_dependency_propagates(self): self.assertEqual(blockers({"a":("b",),"b":()}, {"b":"BUILD_BROKEN"})["a"],("b",))
