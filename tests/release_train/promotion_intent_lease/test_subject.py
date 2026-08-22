import unittest
from scripts.release_train.promotion_intent_lease.subject import Subject,Refusal
class T(unittest.TestCase):
 def test_exact_and_short(self):
  self.assertEqual(Subject.parse('o/r@'+'a'*40).sha,'a'*40)
  with self.assertRaisesRegex(Refusal,'INEXACT_SUBJECT'): Subject.parse('o/r@abc')
