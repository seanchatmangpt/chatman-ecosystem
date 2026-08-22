import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.admission import admit_event
class T(unittest.TestCase):
 def test_orphan_refuses(self):
  a,b,c=Subject("o/a","a"*40),Subject("o/b","b"*40),Subject("o/c","c"*40)
  rows=[Binding(b,a,"1"*64,"s","REPOSITORY","x")]
  with self.assertRaises(Refused): admit_event(rows,InvalidationEvent(c,"BUILD_BROKEN",datetime.now(timezone.utc),"e"))
