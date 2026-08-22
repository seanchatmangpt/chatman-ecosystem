import unittest
from scripts.release_train.promotion_recovery.dependency import DependencyGraph
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_cycle_and_blocker(self):
  with self.assertRaisesRegex(Refusal,'DEPENDENCY_CYCLE'): DependencyGraph({'a':['b'],'b':['a']})
  g=DependencyGraph({'consumer':['producer'],'producer':[]})
  self.assertEqual(g.blocker({'producer':'BUILD_BROKEN'}),'producer')
