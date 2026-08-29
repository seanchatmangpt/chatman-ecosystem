import unittest
from scripts.release_train.provenance_reconciliation.model import ExactSubject, Refused

class SubjectCourt(unittest.TestCase):
    def test_exact_subject_admitted(self): self.assertIn("@", ExactSubject("a/b", "a"*40).coordinate)
    def test_short_sha_refused(self):
        with self.assertRaisesRegex(Refused, "NON_EXACT_SUBJECT"): ExactSubject("a/b", "abc")
    def test_bad_repo_refused(self):
        with self.assertRaisesRegex(Refused, "INVALID_REPOSITORY"): ExactSubject("a", "a"*40)
if __name__ == "__main__": unittest.main()
