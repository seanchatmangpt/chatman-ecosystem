import unittest
from scripts.develop_train.recovery_evidence_quorum.subject import Refused, Subject

class TestSubject(unittest.TestCase):
    def test_exact_subject_and_short_sha_refusal(self):
        self.assertEqual(Subject('o/r', 'a'*40).exact_id, 'o/r@'+'a'*40)
        with self.assertRaisesRegex(Refused, 'INEXACT_SUBJECT_SHA'):
            Subject('o/r', 'a'*8)
