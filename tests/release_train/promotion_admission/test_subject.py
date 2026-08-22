import unittest
from scripts.release_train.promotion_admission.subject import Subject, SubjectRefusal
class T(unittest.TestCase):
    def test_exact_identity(self):
        s=Subject("o/r","a"*40); self.assertEqual(s.identity,"o/r@"+"a"*40)
    def test_short_sha_refuses(self):
        with self.assertRaisesRegex(SubjectRefusal,"INEXACT"): Subject("o/r","a"*39)
if __name__=="__main__": unittest.main()
