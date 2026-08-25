import unittest
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.case import CompositionCase
from scripts.measure_train.evidence_composition_msa.calibration import calibrate
from scripts.measure_train.evidence_composition_msa.sensitivity import sensitivity
class T(unittest.TestCase):
 def test_empirical_coverage_and_dependence_sensitivity(self):
  s=Subject("o/r","a"*40,"b"*64); p=Interval(Fraction(2,5),Fraction(4,5))
  rows=[CompositionCase(s,str(i),p,Fraction(1,2),"UNKNOWN_DEPENDENCE") for i in range(5)]
  c=calibrate(rows); self.assertEqual(c.state,"CALIBRATED")
  d=sensitivity(p,Interval(Fraction(1,2),Fraction(7,10)))
  self.assertGreater(d.endpoint_shift,Fraction(0))
