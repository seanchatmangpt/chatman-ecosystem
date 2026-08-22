import unittest
from scripts.release_train.current_frontier.subject import Subject, Refusal
class T(unittest.TestCase):
 def test_exact_subject(self): self.assertEqual(Subject.parse("o/r@"+"a"*40).canonical(),"o/r@"+"a"*40)
 def test_short_refuses(self):
  with self.assertRaises(Refusal): Subject.parse("o/r@abc")
