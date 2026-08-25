import unittest
from fractions import Fraction
from scripts.develop_train.kantorovich_certificate_realization import *
from test_identity_admission import SUB, CERT, observation

class Chicago(unittest.TestCase):
    def test_certificate_realization_path_and_failure_dominance(self):
        obs = [observation(i) for i in range(11)]
        q = qualify(SUB, CERT, obs)
        self.assertEqual(q.standing, "PARTIAL_ALIVE")
        self.assertEqual(q.worst_false_safe_rate, Fraction(0))
        self.assertEqual(replay(q.receipt, q.receipt.digest), "REPLAY_MATCH")

        red = qualify(SUB, CERT, obs, dependencies=("BUILD_BROKEN",))
        self.assertEqual(red.standing, "BUILD_BROKEN")
        self.assertIsNone(red.receipt)

if __name__ == "__main__": unittest.main()
