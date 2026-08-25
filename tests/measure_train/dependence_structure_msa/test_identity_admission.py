import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.dependence_structure_msa.subject import Subject,Refused
from scripts.measure_train.dependence_structure_msa.observation import PairObservation
from scripts.measure_train.dependence_structure_msa.admission import admit_observations
class T(unittest.TestCase):
 def test_exact_and_duplicate_contradiction(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  a=PairObservation(s,"L","R","x",True,False,"all",now)
  b=PairObservation(s,"L","R","x",False,False,"all",now)
  with self.assertRaises(Refused): admit_observations(s,[a,b],now+timedelta(seconds=1))
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
