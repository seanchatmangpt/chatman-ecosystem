import unittest
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.dependency import dependency_graph
class T(unittest.TestCase):
 def test_cycle_refuses(self):
  a,b=Subject("o/a","a"*40),Subject("o/b","b"*40)
  with self.assertRaises(Refused): dependency_graph([a,b],[(a,b),(b,a)])
