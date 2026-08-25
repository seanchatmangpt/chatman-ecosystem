import unittest
from scripts.measure_train.counterfactual_evaluator_msa.standing import standing
class T(unittest.TestCase):
 def test_ceiling_and_red(self):
  self.assertEqual(standing("COHERENT",["PASS","PASS"]),"PARTIAL_ALIVE")
  self.assertEqual(standing("COHERENT",["PASS"],["BUILD_BROKEN"]),"BLOCKED")
  self.assertEqual(standing("DIVERGED",["PASS"]),"UNKNOWN")
