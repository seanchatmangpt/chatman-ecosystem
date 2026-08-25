import unittest
from scripts.measure_train.cross_control_msa.graph import admit_graph
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_cycle(self):
  with self.assertRaises(Refused): admit_graph(["a","b"],[("a","b"),("b","a")])
