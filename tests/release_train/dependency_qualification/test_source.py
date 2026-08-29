import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.policy import DependencyPolicy
from scripts.release_train.dependency_qualification.source import admit_git_source
class T(unittest.TestCase):
 def test_exact_repo(self): self.assertEqual(admit_git_source(DependencyPolicy(frozenset({'seanchatmangpt/clap-noun-verb'})), 'https://github.com/seanchatmangpt/clap-noun-verb.git'),'seanchatmangpt/clap-noun-verb')
 def test_other_host_refused(self):
  with self.assertRaises(Refusal): admit_git_source(DependencyPolicy(),'ssh://example/r')
