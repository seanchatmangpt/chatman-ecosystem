import unittest
from scripts.release_train.promotion_epoch.subject import Subject, Refusal
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(Subject("o/r","a"*40).key,"o/r@"+"a"*40)
 def test_short_refuses(self):
  with self.assertRaises(Refusal): Subject("o/r","a"*7)
