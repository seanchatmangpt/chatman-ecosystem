import unittest
from scripts.measure_train.replica_quorum_msa.fault import FaultTrial
from scripts.measure_train.replica_quorum_msa.metrics import measure_trials,wilson_lower
class T(unittest.TestCase):
 def test_false_current_is_measured(self):
  rows=[FaultTrial("a","HEALTHY","CURRENT"),FaultTrial("b","PARTITION","CURRENT"),FaultTrial("c","SPLIT_BRAIN","AMBIGUOUS")]
  m=measure_trials(rows); self.assertEqual(m.false_current,1); self.assertEqual(m.ambiguity,1)
  self.assertGreaterEqual(wilson_lower(10,10),0); self.assertLessEqual(wilson_lower(10,10),1)
