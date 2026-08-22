import unittest
from scripts.measure_train.identity import Subject, Refused, RefusalCode
class IdentityCourt(unittest.TestCase):
    def test_exact_subject(self): self.assertEqual(Subject("o/r","a"*40).identity, "o/r@"+"a"*40)
    def test_branch_name_refuses(self):
        with self.assertRaises(Refused) as c: Subject("o/r","main")
        self.assertEqual(c.exception.code, RefusalCode.INVALID_SUBJECT)
    def test_bad_repo_refuses(self):
        with self.assertRaises(Refused): Subject("repo-only","a"*40)
if __name__=='__main__': unittest.main()
