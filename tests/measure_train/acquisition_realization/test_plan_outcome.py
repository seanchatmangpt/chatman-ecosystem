import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.acquisition_realization.subject import Subject,Refused
from scripts.measure_train.acquisition_realization.plan import AcquisitionPlan
from scripts.measure_train.acquisition_realization.outcome import AcquisitionOutcome
class T(unittest.TestCase):
 def test_contracts(self):
  s=Subject("o/r","a"*40)
  p=AcquisitionPlan(s,"p1",1,"MAX_INFORMATION_GAIN","c1",Fraction(1,5),Fraction(4,5),Fraction(2),10,"1"*64)
  o=AcquisitionOutcome(s,"p1","c1",datetime.now(timezone.utc),"PASS",Fraction(1,10),Fraction(2),9,"e1")
  self.assertEqual(p.candidate_id,o.candidate_id)
  with self.assertRaises(Refused): AcquisitionOutcome(s,"p1","c1",datetime.now(),"PASS",Fraction(1,10),1,1,"e")
