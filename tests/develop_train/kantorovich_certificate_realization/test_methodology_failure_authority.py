import unittest
from scripts.develop_train.kantorovich_certificate_realization import *
from test_identity_admission import observation

class MethodologyFailureAuthority(unittest.TestCase):
    def test_methodology_and_failure_census(self):
        obs = [observation(i) for i in range(len(REQUIRED))]
        self.assertEqual(require_methodologies(obs), REQUIRED)
        self.assertEqual(len(require_failure_worlds(list(World))), 7)

    def test_do_requires_brce(self):
        with self.assertRaises(Refused):
            admit_action(Action.DO)
        self.assertEqual(admit_action(Action.DO, "BRCE"), Action.DO)

if __name__ == "__main__": unittest.main()
