import unittest
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.topology import DependencyGraph
class T(unittest.TestCase):
 def test_transitive_depth_and_cycle(self):
  a=Subject("x/a@"+"a"*40); b=Subject("x/b@"+"b"*40); c=Subject("x/c@"+"c"*40); g=DependencyGraph({a:(b,),b:(c,)})
  self.assertEqual(g.affected(a),((b,1),(c,2)))
  with self.assertRaisesRegex(ValueError,"DEPENDENCY_CYCLE"): DependencyGraph({a:(b,),b:(a,)})
