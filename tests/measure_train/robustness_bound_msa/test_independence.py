import unittest
from scripts.measure_train.robustness_bound_msa.independence import IndependenceProof
from scripts.measure_train.robustness_bound_msa.subject import Refused
class T(unittest.TestCase):
 def test_proof(self):
  self.assertTrue(IndependenceProof("a","b",True,True).admit())
  with self.assertRaises(Refused): IndependenceProof("a","b",True,False).admit()
