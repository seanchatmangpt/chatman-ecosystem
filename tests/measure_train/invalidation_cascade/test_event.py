import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
class T(unittest.TestCase):
 def test_time_and_kind(self):
  e=InvalidationEvent(Subject("p/r","a"*40),"BUILD_BROKEN",datetime.now(timezone.utc),"e1")
  self.assertEqual(e.kind,"BUILD_BROKEN")
  with self.assertRaises(Refused): InvalidationEvent(e.producer,"BAD",datetime.now(timezone.utc),"e2")
