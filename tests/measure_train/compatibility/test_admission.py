import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
from scripts.measure_train.compatibility.admission import admit
class T(unittest.TestCase):
 def test_conflict_refuses(self):
  s=Subject("a/b","a"*40); v=EvidenceVector(s,(Evidence(s,Axis.RECEIPT,Outcome.PASS,"2026-08-22T08:00:00Z"),Evidence(s,Axis.RECEIPT,Outcome.FAIL,"2026-08-22T08:01:00Z"))); self.assertFalse(admit(v)["admitted"])
