import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.acquisition_realization.subject import Subject,Refused
from scripts.measure_train.acquisition_realization.plan import AcquisitionPlan
from scripts.measure_train.acquisition_realization.outcome import AcquisitionOutcome
from scripts.measure_train.acquisition_realization.admission import admit_realization
class T(unittest.TestCase):
 def test_stale_policy_and_frontier_refuse(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  p=AcquisitionPlan(s,"p",1,"MAX_INFORMATION_GAIN","c",Fraction(1,5),Fraction(1,2),1,1,"1"*64)
  o=AcquisitionOutcome(s,"p","c",now,"PASS",Fraction(1,10),1,1,"e")
  self.assertEqual(admit_realization(p,o,1,"1"*64,now),"ADMITTED")
  with self.assertRaises(Refused): admit_realization(p,o,2,"1"*64,now)
  with self.assertRaises(Refused): admit_realization(p,o,1,"2"*64,now)
