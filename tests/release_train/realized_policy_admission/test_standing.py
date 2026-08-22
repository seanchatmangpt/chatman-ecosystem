import unittest
from scripts.release_train.realized_policy_admission.standing import bounded_standing
class T(unittest.TestCase):
    def test_failure_dominance(self):
        self.assertEqual(bounded_standing(admitted=True),"PARTIAL_ALIVE")
        self.assertEqual(bounded_standing(admitted=True,blockers=("x",)),"BLOCKED")
        self.assertEqual(bounded_standing(admitted=True,explicit_failure=True),"BUILD_BROKEN")
