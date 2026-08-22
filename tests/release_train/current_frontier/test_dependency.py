import unittest
from scripts.release_train.current_frontier.dependency import dependency_order, propagate, Refusal
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(dependency_order({"app":("lib",),"lib":()}, {"app","lib"}),("lib","app"))
 def test_cycle(self):
  with self.assertRaises(Refusal): dependency_order({"a":("b",),"b":("a",)}, {"a","b"})
 def test_blocker_propagates(self): self.assertEqual(propagate({"lib":"BUILD_BROKEN","app":"PARTIAL_ALIVE"},{"app":("lib",),"lib":()},("lib","app"))["app"],"BLOCKED")
