import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.graph import dependency_closure
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(dependency_closure('app',{'app':('lib',),'lib':()}),('lib','app'))
 def test_cycle(self):
  with self.assertRaises(Refusal): dependency_closure('a',{'a':('b',),'b':('a',)})
