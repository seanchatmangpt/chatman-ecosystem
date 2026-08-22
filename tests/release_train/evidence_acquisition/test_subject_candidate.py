import unittest

from scripts.release_train.evidence_acquisition.candidate import EvidenceCandidate
from scripts.release_train.evidence_acquisition.subject import Subject

class SubjectCandidateCourt(unittest.TestCase):
    def test_exact_subject_and_authority(self):
        subject = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        self.assertEqual(subject.repo, "seanchatmangpt/chatman-ecosystem")
        with self.assertRaisesRegex(ValueError, "INEXACT_SUBJECT"):
            Subject.parse("seanchatmangpt/chatman-ecosystem@abc")
        with self.assertRaisesRegex(ValueError, "BRCE_REQUIRED"):
            EvidenceCandidate("x", "fam", "runtime", "repo", 1, 1, authority="DO")

if __name__ == "__main__":
    unittest.main()
