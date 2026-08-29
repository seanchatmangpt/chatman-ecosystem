import unittest
from scripts.release_train.promotion_recovery.subject import Subject,Refusal
class T(unittest.TestCase):
 def test_exact_subject(self):
  self.assertEqual(Subject('o/r','a'*40).identity,'o/r@'+'a'*40)
  with self.assertRaisesRegex(Refusal,'INEXACT_SUBJECT'): Subject('o/r','abc')
