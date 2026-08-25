import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject
from scripts.measure_train.process_intelligence_correspondence_msa.rail import RailEvidence
from scripts.measure_train.process_intelligence_correspondence_msa.trace import trace_equivalence
class T(unittest.TestCase):
 def test_divergence(self):
  s=Subject("o/r","a"*40); sem="b"*64
  rows=[RailEvidence(s,"a","POWL",sem,"c"*64,"PASS"),RailEvidence(s,"b","REACTOR",sem,"d"*64,"PASS")]
  self.assertEqual(trace_equivalence(rows),"DIVERGENT")
