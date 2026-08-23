import unittest
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject,Refused
class T(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(Subject("o/r","a"*40,1).generation,1)
  with self.assertRaises(Refused): Subject("o/r","bad",1)
