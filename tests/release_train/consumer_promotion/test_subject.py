import unittest
from scripts.release_train.consumer_promotion.subject import Subject
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(Subject("o/r","a"*40).key,"o/r@"+"a"*40)
 def test_refuse(self):
  with self.assertRaisesRegex(ValueError,"INEXACT_SHA"): Subject("o/r","main")
