import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
from scripts.measure_train.compatibility.compatibility import classify
class T(unittest.TestCase):
 def test_diverged(self):
  s=Subject("a/b","a"*40); a=EvidenceVector(s,(Evidence(s,Axis.REPOSITORY,Outcome.PASS,"2026-08-22T08:00:00Z"),)); b=EvidenceVector(s,(Evidence(s,Axis.REPOSITORY,Outcome.FAIL,"2026-08-22T08:01:00Z"),)); self.assertEqual(classify(a,b),"DIVERGED")
