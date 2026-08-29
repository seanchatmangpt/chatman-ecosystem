import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.policy import DependencyPolicy
class T(unittest.TestCase):
 def test_allow_and_refuse(self):
  p=DependencyPolicy(frozenset({'seanchatmangpt/clap-noun-verb'}),frozenset({'MIT'})); p.admit_repo('seanchatmangpt/clap-noun-verb'); p.admit_license('MIT')
  with self.assertRaises(Refusal): p.admit_repo('evil/r')
