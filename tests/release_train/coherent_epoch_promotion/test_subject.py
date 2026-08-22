import unittest
from scripts.release_train.coherent_epoch_promotion.subject import Subject
class T(unittest.TestCase):
 def test_exact_only(self):
  self.assertEqual(Subject.parse('o/r@'+'a'*40).sha,'a'*40)
  with self.assertRaisesRegex(ValueError,'INEXACT_SUBJECT'): Subject.parse('o/r@abc')
