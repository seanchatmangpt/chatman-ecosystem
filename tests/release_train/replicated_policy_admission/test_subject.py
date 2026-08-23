import unittest
from scripts.release_train.replicated_policy_admission.subject import Subject
from scripts.release_train.replicated_policy_admission.refusal import Refused
class TestSubject(unittest.TestCase):
    def test_exact(self): self.assertEqual(Subject('a/b','0'*40).identity,'a/b@'+'0'*40)
    def test_short_refuses(self):
        with self.assertRaisesRegex(Refused,'INEXACT_SUBJECT'): Subject('a/b','abc')
