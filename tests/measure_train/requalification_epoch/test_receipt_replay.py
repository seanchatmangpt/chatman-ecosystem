import unittest
from datetime import datetime,timezone
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.receipt import manufacture_receipt
from scripts.measure_train.requalification_epoch.replay import replay
class T(unittest.TestCase):
 def test_deterministic_tamper_sensitive_no_do(self):
  e=InvalidationEpoch(Subject("p/r","a"*40),1,"e",datetime(2026,8,22,tzinfo=timezone.utc),"1"*64); rows=(("c/r","b"*40,"REQUALIFIED"),)
  a=manufacture_receipt(e,rows,"PARTIAL_ALIVE"); b=manufacture_receipt(e,rows,"PARTIAL_ALIVE"); self.assertEqual(a,b); self.assertEqual(replay(a),"REPLAY_MATCH"); self.assertFalse(a["body"]["actuation_performed"])
  a["body"]["generation"]=2
  with self.assertRaises(Refused): replay(a)
