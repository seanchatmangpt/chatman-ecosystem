import unittest
from scripts.release_train.calibrated_composition_crown import *
class T(unittest.TestCase):
 def test_graph_and_topology(self):
  g=DependencyGraph({"root":["a"],"a":[]}); self.assertEqual(g.blockers({"a":"BUILD_BROKEN"},"root"),("a",))
  with self.assertRaises(Refused): DependencyGraph({"a":["b"],"b":["a"]}).order()
  self.assertEqual(len(METHODS),11); self.assertEqual(len(RAILS),9); self.assertEqual(len(FAILURES),7)
