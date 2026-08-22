import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.acquisition_realization.subject import Subject,Refused
from scripts.measure_train.acquisition_realization.plan import AcquisitionPlan
from scripts.measure_train.acquisition_realization.outcome import AcquisitionOutcome
from scripts.measure_train.acquisition_realization.qualify import qualify
from scripts.measure_train.acquisition_realization.replay import replay
class T(unittest.TestCase):
 def test_realized_voi_currentness_and_no_do(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); records=[]
  for i in range(5):
   p=AcquisitionPlan(s,f"p{i}",3,"MAX_INFORMATION_GAIN",f"c{i}",Fraction(7,10),Fraction(4,5),Fraction(2),100,"1"*64)
   o=AcquisitionOutcome(s,f"p{i}",f"c{i}",now-timedelta(seconds=i),"PASS",Fraction(1,20),Fraction(2),90,f"e{i}")
   records.append((p,o,0.0))
  q=qualify(s,Fraction(1,2),records,3,"1"*64,now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  with self.assertRaises(Refused): qualify(s,Fraction(1,2),records,4,"1"*64,now)
