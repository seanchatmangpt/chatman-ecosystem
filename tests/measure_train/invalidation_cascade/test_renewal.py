import unittest
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.renewal import renew
class T(unittest.TestCase):
 def test_schema_drift_refuses(self):
  a,b=Subject("o/a","a"*40),Subject("o/b","b"*40); x=Binding(b,a,"1"*64,"s/1","REPOSITORY","x")
  with self.assertRaises(Refused): renew(x,a,"2"*64,"s/2")
