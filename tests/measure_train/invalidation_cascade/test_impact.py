import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.impact import direct_impact
class T(unittest.TestCase):
 def test_reason(self):
  a,b=Subject("o/a","a"*40),Subject("o/b","b"*40)
  rows=[Binding(b,a,"1"*64,"s","REPOSITORY","x")]
  self.assertEqual(direct_impact(rows,InvalidationEvent(a,"NEW_RECEIPT",datetime.now(timezone.utc),"e","2"*64))[0][1],"PRODUCER_RECEIPT_SUPERSEDED")
