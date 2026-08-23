import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject
from scripts.measure_train.process_intelligence_correspondence_msa.rail import RailEvidence
from scripts.measure_train.process_intelligence_correspondence_msa.methodology import REQUIRED
from scripts.measure_train.process_intelligence_correspondence_msa.qualify import qualify
from scripts.measure_train.process_intelligence_correspondence_msa.replay import replay
class T(unittest.TestCase):
 def test_chicago(self):
  s=Subject("o/r","a"*40); sem="b"*64; tr="c"*64
  rails=[RailEvidence(s,"powl","POWL",sem,tr,"PASS"),RailEvidence(s,"reactor","REACTOR",sem,tr,"PASS"),RailEvidence(s,"ci","CI",sem,tr,"PASS")]
  q=qualify(s,rails,REQUIRED,"AGREE","CURRENT","UNOBSERVED")
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
