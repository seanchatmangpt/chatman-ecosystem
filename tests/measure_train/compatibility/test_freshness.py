import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.evidence_axis import Axis,Outcome
from scripts.measure_train.compatibility.vector import Evidence
from scripts.measure_train.compatibility.freshness import stale
class T(unittest.TestCase):
 def test_future_refuses(self):
  s=Subject("a/b","a"*40); r=Evidence(s,Axis.FOCUSED,Outcome.PASS,"2026-08-22T08:10:01Z")
  with self.assertRaises(ValueError): stale(r,"2026-08-22T08:10:00Z",60)
