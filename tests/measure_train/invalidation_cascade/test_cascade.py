import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_cascade.subject import Subject
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.event import InvalidationEvent
from scripts.measure_train.invalidation_cascade.cascade import cascade
class T(unittest.TestCase):
 def test_transitive_depth(self):
  a,b,c=Subject("o/a","a"*40),Subject("o/b","b"*40),Subject("o/c","c"*40)
  rows=[Binding(b,a,"1"*64,"s","REPOSITORY","ab"),Binding(c,b,"2"*64,"s","REPOSITORY","bc")]
  self.assertEqual(cascade(rows,InvalidationEvent(a,"BUILD_BROKEN",datetime.now(timezone.utc),"e")),(("ab",1),("bc",2)))
