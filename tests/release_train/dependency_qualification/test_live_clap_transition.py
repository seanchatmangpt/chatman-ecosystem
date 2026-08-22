import unittest
from scripts.release_train.dependency_qualification import DependencySubject
from scripts.release_train.dependency_qualification.pin import PinTransition

class T(unittest.TestCase):
 def test_observed_descendant_transition(self):
  current=DependencySubject('seanchatmangpt/clap-noun-verb','a0f9f79b88e454742ec7c17c91ca31837cabc2c8')
  candidate=DependencySubject('seanchatmangpt/clap-noun-verb','31e55ec0440f48b91ff6c5e08b0946c837b98c63')
  self.assertEqual(PinTransition(current,candidate,'descendant').admit(),candidate)
