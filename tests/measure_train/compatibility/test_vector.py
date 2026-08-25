import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence,EvidenceVector
class T(unittest.TestCase):
 def test_foreign_row_refuses(self):
  a=Subject("a/b","a"*40); b=Subject("a/b","b"*40)
  with self.assertRaises(ValueError): EvidenceVector(a,(Evidence(b,Axis.FOCUSED,Outcome.PASS,"2026-08-22T08:00:00Z"),))
