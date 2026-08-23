import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_correspondence_msa.receipt import manufacture
from scripts.measure_train.process_intelligence_correspondence_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture(Subject("o/r","a"*40),{"x":1},"UNKNOWN"); self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
