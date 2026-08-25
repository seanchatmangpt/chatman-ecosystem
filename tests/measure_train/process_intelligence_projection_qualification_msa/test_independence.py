import unittest
from scripts.measure_train.process_intelligence_projection_qualification_msa.independence import IndependenceWitness
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_independence_explicit(self):
        self.assertTrue(IndependenceWitness('a','b',True,True,True).admit())
        with self.assertRaises(Refused): IndependenceWitness('a','b',True,False,True).admit()
