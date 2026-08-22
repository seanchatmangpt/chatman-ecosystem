import unittest
from scripts.release_train.subject import Subject, SubjectRefusal

class SubjectTests(unittest.TestCase):
    def test_admits_exact_subject(self):
        s = Subject.admit("seanchatmangpt/gymact", "a"*40)
        self.assertEqual(s.repo, "seanchatmangpt/gymact")

    def test_refuses_branch_name_as_sha(self):
        with self.assertRaisesRegex(SubjectRefusal, "INVALID_EXACT_SHA"):
            Subject.admit("seanchatmangpt/gymact", "main")

    def test_refuses_malformed_repo(self):
        with self.assertRaisesRegex(SubjectRefusal, "INVALID_REPOSITORY_IDENTITY"):
            Subject.admit("gymact", "a"*40)
