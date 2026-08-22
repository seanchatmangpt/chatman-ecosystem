import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.acquisition_realization.subject import Subject,Refused
from scripts.measure_train.acquisition_realization.plan import AcquisitionPlan
from scripts.measure_train.acquisition_realization.outcome import AcquisitionOutcome
from scripts.measure_train.acquisition_realization.realization import realize
class T(unittest.TestCase):
 def test_identity_binding(self):
  s=Subject("o/r","a"*40); p=AcquisitionPlan(s,"p",1,"MAX_INFORMATION_GAIN","c",Fraction(1,5),Fraction(3,4),1,1,"1"*64)
  o=AcquisitionOutcome(s,"p","c",datetime.now(timezone.utc),"PASS",Fraction(1,20),1,1,"e")
  self.assertEqual(realize(p,o,Fraction(1,2)).sign,"POSITIVE")
  o2=AcquisitionOutcome(s,"x","c",datetime.now(timezone.utc),"PASS",Fraction(1,20),1,1,"e2")
  with self.assertRaises(Refused): realize(p,o2,Fraction(1,2))
