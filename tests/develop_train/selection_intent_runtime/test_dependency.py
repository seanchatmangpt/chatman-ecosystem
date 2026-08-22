import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.dependency import DependencyGraph
class TestDependency(unittest.TestCase):
 def test_transitive_blocker_and_cycle(self):
  a=Subject("a/a@"+"a"*40); b=Subject("a/b@"+"b"*40); c=Subject("a/c@"+"c"*40); g=DependencyGraph(((a,b),(b,c))); self.assertEqual(g.blocked({a:"BUILD_BROKEN",b:"PARTIAL_ALIVE",c:"PARTIAL_ALIVE"}),{a,b,c})
  with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"): DependencyGraph(((a,b),(b,a)))
