import unittest
from scripts.release_train.realized_policy_admission.subject import Subject
class T(unittest.TestCase):
    def test_exact(self):
        s=Subject("o/r","a"*40); self.assertEqual(s.identity,"o/r@"+"a"*40)
        with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("o/r","abc")
