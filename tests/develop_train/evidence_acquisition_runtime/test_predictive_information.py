import unittest
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.predictive import Belief,posterior_defect
from scripts.develop_train.evidence_acquisition_runtime.information import expected_information_gain
class T(unittest.TestCase):
 def test_information_direction(self):
  b=Belief(Fraction(1,4),1); hit=posterior_defect(b,tpr=Fraction(9,10),fpr=Fraction(1,10),detects=True); clean=posterior_defect(b,tpr=Fraction(9,10),fpr=Fraction(1,10),detects=False)
  self.assertGreater(hit,b.defect); self.assertLess(clean,b.defect); self.assertGreater(expected_information_gain(b,tpr=Fraction(9,10),fpr=Fraction(1,10)),0)
  self.assertAlmostEqual(expected_information_gain(b,tpr=Fraction(1,2),fpr=Fraction(1,2)),0.0,places=12)
