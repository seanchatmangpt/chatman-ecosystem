import unittest
from scripts.release_train.promotion_epoch.graph import DependencyGraph,GraphRefusal
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(DependencyGraph((("b","a"),)).order(("a","b")),("a","b"))
 def test_cycle(self):
  with self.assertRaises(GraphRefusal): DependencyGraph((("a","b"),("b","a"))).order(("a","b"))
