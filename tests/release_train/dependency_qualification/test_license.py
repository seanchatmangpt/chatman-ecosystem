import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.license import admit_licenses
from scripts.release_train.dependency_qualification.policy import DependencyPolicy
class T(unittest.TestCase):
 def test_explicit_cc0(self): self.assertEqual(admit_licenses(DependencyPolicy(allowed_licenses=frozenset({'CC0-1.0'})),{'notify':'CC0-1.0'}),(('notify','CC0-1.0'),))
 def test_empty_refused(self):
  with self.assertRaises(Refusal): admit_licenses(DependencyPolicy(),{})
