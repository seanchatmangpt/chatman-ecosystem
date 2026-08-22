import unittest
from scripts.release_train.calibrated_recovery_quorum.subject import Subject,Refused
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(Subject("o/r","a"*40).exact,"o/r@"+"a"*40)
 def test_short_refuses(self):
  with self.assertRaises(Refused): Subject("o/r","abc")
