import unittest
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject,Refused
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.case import CompositionCase
from scripts.measure_train.evidence_composition_msa.calibration import CompositionCalibration
from scripts.measure_train.evidence_composition_msa.methodology import REQUIRED,require_complete
from scripts.measure_train.evidence_composition_msa.admission import admit_case
class T(unittest.TestCase):
 def test_full_methodology_and_width_gate(self):
  self.assertTrue(require_complete(REQUIRED)["complete"])
  s=Subject("o/r","a"*40,"b"*64)
  c=CompositionCase(s,"x",Interval(Fraction(0),Fraction(1)),Fraction(1,2),"UNKNOWN_DEPENDENCE")
  cal=CompositionCalibration(10,Fraction(1),Fraction(0),Fraction(1),"CALIBRATED")
  with self.assertRaises(Refused): admit_case(s,c,cal,max_width=Fraction(1,2))
