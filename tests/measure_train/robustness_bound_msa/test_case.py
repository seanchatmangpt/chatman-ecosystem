import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.subject import Subject
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.case import BoundCase
class T(unittest.TestCase):
 def test_coverage(self):
  c=BoundCase(Subject("o/r","a"*40),RobustnessBound(Fraction(0),Fraction(1),Fraction(1),"IPS","a"*64),Fraction(1,2),"e",datetime.now(timezone.utc))
  self.assertTrue(c.covers)
