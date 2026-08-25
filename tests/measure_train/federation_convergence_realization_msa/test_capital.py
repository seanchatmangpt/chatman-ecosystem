import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.capital import Source,effective
class T(unittest.TestCase):
 def test_duplicate_collapse(self):
  rows=[Source(str(i),'a'*64,'b'*64,'same') for i in range(3)]
  self.assertEqual(effective(rows,Fraction(1)),Fraction(1))
