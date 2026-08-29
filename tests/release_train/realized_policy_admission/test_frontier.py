import unittest
from scripts.release_train.realized_policy_admission.policy import Policy
from scripts.release_train.realized_policy_admission.frontier import PolicyFrontier,admit_frontier
class T(unittest.TestCase):
    def test_current_and_stale(self):
        p=Policy(2,2,.2,2,2,.5); f=PolicyFrontier(2,p.digest,"b"*64)
        self.assertIs(admit_frontier(f,p),f)
        with self.assertRaisesRegex(ValueError,"STALE_POLICY_FRONTIER"):
            admit_frontier(f,Policy(3,2,.2,2,2,.5))
