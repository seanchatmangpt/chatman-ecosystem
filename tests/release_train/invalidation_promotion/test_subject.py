import unittest
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
class T(unittest.TestCase):
 def test_exact_and_refusal(self):
  self.assertEqual(Subject('a/b','a'*40).key,'a/b@'+'a'*40)
  with self.assertRaises(Refusal): Subject('a/b','main')
