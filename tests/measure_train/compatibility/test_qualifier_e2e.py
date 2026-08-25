import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
from scripts.measure_train.compatibility.qualifier import qualify
from scripts.measure_train.compatibility.replay import replay
class T(unittest.TestCase):
 def test_e2e_no_do(self):
  s=Subject("a/b","a"*40); v=EvidenceVector(s,(Evidence(s,Axis.FOCUSED,Outcome.PASS,"2026-08-22T08:00:00Z"),)); q=qualify(v); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
