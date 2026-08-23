import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject
from scripts.measure_train.process_intelligence_correspondence_msa.rail import RailEvidence
from scripts.measure_train.process_intelligence_correspondence_msa.correspondence import admit_correspondence
class T(unittest.TestCase):
 def test_order_invariant(self):
  s=Subject("o/r","a"*40); sem="b"*64; tr="c"*64
  a=RailEvidence(s,"a","POWL",sem,tr,"PASS"); b=RailEvidence(s,"b","REACTOR",sem,tr,"PASS")
  self.assertEqual(admit_correspondence(s,[a,b]),admit_correspondence(s,[b,a]))
