import unittest
from scripts.release_train.dependency_qualification import DependencySubject, Refusal
from scripts.release_train.dependency_qualification.pin import PinTransition
class T(unittest.TestCase):
 def test_descendant(self): self.assertEqual(PinTransition(DependencySubject('o/r','a'*40),DependencySubject('o/r','b'*40),'descendant').admit().sha,'b'*40)
 def test_unknown_ancestry(self):
  with self.assertRaises(Refusal): PinTransition(DependencySubject('o/r','a'*40),DependencySubject('o/r','b'*40),'unknown').admit()
