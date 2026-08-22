import unittest
from scripts.develop_train.epoch_discharge.identity import Subject
class T(unittest.TestCase):
 def test_exact_subject_only(self):
  self.assertEqual(Subject("a/b@"+"a"*40).sha,"a"*40)
  with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("a/b@abc")
