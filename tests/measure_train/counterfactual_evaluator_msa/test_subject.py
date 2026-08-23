import unittest
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_exact(self):
  self.assertEqual(Subject("o/r","a"*40).sha,"a"*40)
  with self.assertRaises(Refused): Subject("o/r","abc")
