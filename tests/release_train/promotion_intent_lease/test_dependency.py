import unittest
from scripts.release_train.promotion_intent_lease.dependency import DependencyGraph
from scripts.release_train.promotion_intent_lease.subject import Refusal
from _helpers import S1,S2
class T(unittest.TestCase):
 def test_order_and_cycle(self):
  self.assertEqual(DependencyGraph(((S1,S2),)).closure(S1),(S2,S1))
  with self.assertRaisesRegex(Refusal,'DEPENDENCY_CYCLE'): DependencyGraph(((S1,S2),(S2,S1))).closure(S1)
