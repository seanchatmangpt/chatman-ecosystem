import unittest
from scripts.release_train.realized_policy_admission.policy import Policy
class T(unittest.TestCase):
    def test_digest_generation_bound(self):
        a=Policy(1,2,.2,2,2,.5); b=Policy(2,2,.2,2,2,.5)
        self.assertEqual(a.digest,a.digest); self.assertNotEqual(a.digest,b.digest)
