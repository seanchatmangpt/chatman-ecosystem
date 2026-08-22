import unittest
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.binding import Binding
class T(unittest.TestCase):
 def test_receipt_and_scope(self):
  b=Binding(Subject("c/r","b"*40),Subject("p/r","a"*40),"1"*64,"s/1","REPOSITORY","b1")
  self.assertEqual(b.scope,"REPOSITORY")
  with self.assertRaises(Refused): Binding(b.consumer,b.producer,"bad","s/1","REPOSITORY","b2")
