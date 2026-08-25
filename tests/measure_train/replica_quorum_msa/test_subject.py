import unittest
from scripts.measure_train.replica_quorum_msa.subject import Subject,Refused
class T(unittest.TestCase):
 def test_exact_subject(self):
  self.assertEqual(Subject("o/r","a"*40).sha,"a"*40)
  with self.assertRaises(Refused): Subject("o/r","abc")
