import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.subject import Subject
from scripts.measure_train.transport_invariance_realization_msa.stress import StressIdentity
from scripts.measure_train.transport_invariance_realization_msa.case import RealizationCase
from scripts.measure_train.transport_invariance_realization_msa.admission import admit_cases
from scripts.measure_train.transport_invariance_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_exact_subject_generation_and_duplicate_correspondence(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); st=StressIdentity("s1","SUPPORT_EROSION",Fraction(1,10),2)
  c=RealizationCase(s,st,True,Fraction(1,10),True,Fraction(1,10),"DISCOVERY","BEAM","us-a","r1","c1",now)
  self.assertEqual(admit_cases(s,[c,c],now,2),(c,))
  with self.assertRaises(Refused): admit_cases(Subject("o/r","c"*40,"b"*64),[c],now,2)
  with self.assertRaises(Refused): admit_cases(s,[c],now,3)
  future=RealizationCase(s,st,True,Fraction(1,10),True,Fraction(1,10),"DISCOVERY","BEAM","us-a","r1","c2",now+timedelta(seconds=2))
  with self.assertRaises(Refused): admit_cases(s,[future],now,2)
