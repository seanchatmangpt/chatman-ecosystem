import unittest
from scripts.measure_train.delta.dependency import DependencyDelta
class T(unittest.TestCase):
 def test_divergence_not_forward(self):
  self.assertEqual(DependencyDelta("x","a"*40,"b"*40,"DIVERGED").classify(),"DIVERGED")
