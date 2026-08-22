import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.event import Invalidation
from scripts.measure_train.invalidation_ack.receipt import manufacture_receipt
from scripts.measure_train.invalidation_ack.replay import replay
class T(unittest.TestCase):
 def test_deterministic_tamper_and_no_do(self):
  e=Invalidation(Subject("p/r","a"*40),"e","BUILD_BROKEN",datetime(2026,8,22,tzinfo=timezone.utc))
  r=manufacture_receipt(e,[],"UNKNOWN"); self.assertEqual(replay(r),"REPLAY_MATCH"); self.assertFalse(r["body"]["actuation_performed"])
  r["body"]["standing"]="PARTIAL_ALIVE"
  with self.assertRaises(Refused): replay(r)
