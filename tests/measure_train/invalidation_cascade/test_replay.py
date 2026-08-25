import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.receipt import manufacture_receipt
from scripts.measure_train.invalidation_cascade.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture_receipt(InvalidationEvent(Subject("o/a","a"*40),"BUILD_BROKEN",datetime.now(timezone.utc),"e"),[],"BLOCKED")
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="PARTIAL_ALIVE"
  with self.assertRaises(Refused): replay(r)
