import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  e=InvalidationEvent(Subject("o/a","a"*40),"BUILD_BROKEN",datetime(2026,8,22,tzinfo=timezone.utc),"e")
  a=manufacture_receipt(e,[("x",1)],"BLOCKED"); b=manufacture_receipt(e,[("x",1)],"BLOCKED")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
