import unittest
from fractions import Fraction
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.subject import Refused
class T(unittest.TestCase):
 def test_do_refuses(self):
  MeasurementCandidate("a","fam","dom","REPOSITORY",Fraction(1),10,"OBSERVE")
  with self.assertRaises(Refused): MeasurementCandidate("b","fam","dom","REPOSITORY",Fraction(1),10,"DO")
