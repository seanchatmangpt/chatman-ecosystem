import unittest
from scripts.release_train.calibrated_recovery_quorum.dependencies import DependencyGraph
class T(unittest.TestCase):
 def test_blockers_and_cycle(self):
  g=DependencyGraph({"a":["b"]}); self.assertEqual(g.blockers("a",{"b":"BUILD_BROKEN"}),["b"])
  with self.assertRaises(Exception): DependencyGraph({"a":["b"],"b":["a"]}).order("a")
