import unittest
from scripts.release_train.sequential_horizon_admission import Subject,ControllerIdentity,Refused
class T(unittest.TestCase):
 def test_exact_identity(self):
  Subject('o/r@'+'a'*40); ControllerIdentity(1,'b'*64,2,'c'*64)
  with self.assertRaises(Refused): Subject('o/r@short')
