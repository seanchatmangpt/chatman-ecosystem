import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.state import classify_binding,aggregate
class T(unittest.TestCase):
 def test_failure_blocks(self):
  a,b=Subject("o/a","a"*40),Subject("o/b","b"*40); x=Binding(b,a,"1"*64,"s","REPOSITORY","x")
  self.assertEqual(classify_binding(x,InvalidationEvent(a,"BUILD_BROKEN",datetime.now(timezone.utc),"e")),"BLOCKED")
  self.assertEqual(aggregate(["BLOCKED"]),"BLOCKED")
