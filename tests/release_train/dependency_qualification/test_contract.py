import unittest
from scripts.release_train.dependency_qualification import DependencySubject, Refusal
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(DependencySubject('o/r','a'*40).key,'o/r@'+'a'*40)
 def test_refuse_short(self):
  with self.assertRaises(Refusal): DependencySubject('o/r','abc')
