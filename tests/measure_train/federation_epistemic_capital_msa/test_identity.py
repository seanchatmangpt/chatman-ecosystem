import unittest
from scripts.measure_train.federation_epistemic_capital_msa.subject import Subject
from scripts.measure_train.federation_epistemic_capital_msa.refusal import Refused
class T(unittest.TestCase):
 def test_exact(self):
  self.assertEqual(Subject("o/r","a"*40,"b"*64).repo,"o/r")
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
