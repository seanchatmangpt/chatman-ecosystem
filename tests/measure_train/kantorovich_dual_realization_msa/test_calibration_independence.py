import unittest
from fractions import Fraction
from scripts.measure_train.kantorovich_dual_realization_msa.feasibility import Feasibility
from scripts.measure_train.kantorovich_dual_realization_msa.differential import Differential
from scripts.measure_train.kantorovich_dual_realization_msa.realization import Realization
from scripts.measure_train.kantorovich_dual_realization_msa.calibration import calibrate
from scripts.measure_train.kantorovich_dual_realization_msa.independence import IndependenceWitness
from scripts.measure_train.kantorovich_dual_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_calibrated_and_independence(self):
  c=calibrate(Feasibility(3,True,True,True,Fraction(0)),Differential(Fraction(0),Fraction(0),Fraction(0)),Realization(Fraction(0),Fraction(0),3))
  self.assertEqual(c.state,"CALIBRATED"); self.assertTrue(IndependenceWitness("a","b","m1","m2").admit())
  with self.assertRaises(Refused): IndependenceWitness("a","a","m1","m2").admit()
