import unittest
from scripts.measure_train.invalidation_cascade.subject import Subject,Refused
from scripts.measure_train.invalidation_cascade.binding import Binding
from scripts.measure_train.invalidation_cascade.graph import build_graph
class T(unittest.TestCase):
 def test_cycle_refuses(self):
  a,b=Subject("o/a","a"*40),Subject("o/b","b"*40)
  rows=[Binding(b,a,"1"*64,"s","REPOSITORY","x"),Binding(a,b,"2"*64,"s","REPOSITORY","y")]
  with self.assertRaises(Refused): build_graph(rows)
