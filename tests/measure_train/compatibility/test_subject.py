import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(Subject("a/b","a"*40).sha,"a"*40)
 def test_short_refuses(self):
  with self.assertRaises(ValueError): Subject("a/b","abc")
