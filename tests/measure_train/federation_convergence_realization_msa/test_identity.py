import unittest
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.refusals import Refused
class T(unittest.TestCase):
 def test_exact(self):
  self.assertEqual(Subject('o/r','a'*40,'b'*64,1).generation,1)
  with self.assertRaises(Refused): Subject('o/r','bad','b'*64,1)
