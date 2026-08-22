import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.authority import admit_action
from scripts.release_train.dependency_qualification.policy import DependencyPolicy
class T(unittest.TestCase):
 def test_construct(self): self.assertEqual(admit_action(DependencyPolicy(),'CONSTRUCT'),'CONSTRUCT')
 def test_do_refused(self):
  with self.assertRaises(Refusal): admit_action(DependencyPolicy(),'DO')
