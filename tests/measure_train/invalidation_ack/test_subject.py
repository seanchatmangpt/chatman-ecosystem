import unittest
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
class T(unittest.TestCase):
 def test_exact(self):
  self.assertEqual(Subject("o/r","a"*40).sha,"a"*40)
  with self.assertRaises(Refused): Subject("o/r","abc")
