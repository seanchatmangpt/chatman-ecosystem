import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_correspondence_msa.rail import RailEvidence
from scripts.measure_train.process_intelligence_correspondence_msa.correspondence import admit_correspondence
class T(unittest.TestCase):
 def test_semantic_drift(self):
  s=Subject("o/r","a"*40)
  rows=[RailEvidence(s,"a","POWL","b"*64,"c"*64,"PASS"),RailEvidence(s,"b","REACTOR","d"*64,"c"*64,"PASS")]
  with self.assertRaises(Refused): admit_correspondence(s,rows)
