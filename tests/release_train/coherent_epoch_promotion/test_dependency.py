import unittest
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.dependency import DependencyGraph
class T(unittest.TestCase):
 def test_cycle_refuses(self):
  a=Subject.parse('o/a@'+'a'*40); b=Subject.parse('o/b@'+'b'*40); g=DependencyGraph(); g.add(a,b)
  with self.assertRaisesRegex(ValueError,'DEPENDENCY_CYCLE'): g.add(b,a)
