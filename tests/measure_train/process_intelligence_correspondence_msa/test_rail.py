import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_correspondence_msa.rail import RailEvidence
class T(unittest.TestCase):
 def test_kind(self):
  s=Subject("o/r","a"*40); RailEvidence(s,"r","POWL","b"*64,"c"*64,"PASS")
  with self.assertRaises(Refused): RailEvidence(s,"r","MAGIC","b"*64,"c"*64,"PASS")
