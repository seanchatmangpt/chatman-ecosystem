import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
from scripts.measure_train.compatibility.projection import ocel
class T(unittest.TestCase):
 def test_exact_subject_preserved(self):
  s=Subject("a/b","a"*40); v=EvidenceVector(s,(Evidence(s,Axis.RUNTIME,Outcome.PASS,"2026-08-22T08:00:00Z"),)); self.assertIn("a"*40,ocel(v)[0])
