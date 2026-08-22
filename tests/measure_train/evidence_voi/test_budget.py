import unittest
from fractions import Fraction
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.budget import AcquisitionBudget,fits_budget
class T(unittest.TestCase):
 def test_all_axes(self):
  a=MeasurementCandidate("a","f","d","REPOSITORY",Fraction(2),50); b=MeasurementCandidate("b","g","e","REPOSITORY",Fraction(2),200)
  budget=AcquisitionBudget(Fraction(3),100,2)
  self.assertTrue(fits_budget([],a,budget)); self.assertFalse(fits_budget([a],b,budget))
