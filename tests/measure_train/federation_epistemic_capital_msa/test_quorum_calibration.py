import unittest
from fractions import Fraction
from scripts.measure_train.federation_epistemic_capital_msa.quorum import QuorumRealization
from scripts.measure_train.federation_epistemic_capital_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_pseudo_quorum_is_error(self):
  rows=[QuorumRealization(4,1.0,2.0,True,True,False,"PSEUDO_QUORUM") for _ in range(5)]; c=calibrate(rows,max_pseudo=Fraction(0)); self.assertEqual(c.state,"UNRELIABLE"); self.assertEqual(c.pseudo_quorum,Fraction(1))
