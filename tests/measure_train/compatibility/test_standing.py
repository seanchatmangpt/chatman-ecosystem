import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
from scripts.measure_train.compatibility.compatibility import standing
class T(unittest.TestCase):
 def test_mixed_failure(self):
  s=Subject("a/b","a"*40); v=EvidenceVector(s,(Evidence(s,Axis.FOCUSED,Outcome.PASS,"2026-08-22T08:00:00Z"),Evidence(s,Axis.REPOSITORY,Outcome.FAIL,"2026-08-22T08:00:00Z"))); self.assertEqual(standing(v),"BUILD_BROKEN")
