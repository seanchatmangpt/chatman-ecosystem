import unittest
from scripts.develop_train.replicated_evidence_state.subject import Subject
from scripts.develop_train.replicated_evidence_state.errors import Refused

class SubjectTest(unittest.TestCase):
    def test_exact_identity_and_short_sha_refusal(self):
        self.assertEqual(Subject("o/r","a"*40).identity,"o/r@"+"a"*40)
        with self.assertRaises(Refused): Subject("o/r","abc")
