import unittest
from datetime import datetime,timezone
from scripts.measure_train.dependence_structure_msa.subject import Subject
from scripts.measure_train.dependence_structure_msa.observation import PairObservation
from scripts.measure_train.dependence_structure_msa.conditional import conditional_profile
class T(unittest.TestCase):
 def test_profile_is_stratified(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[]
  vals=[("a",0,0),("a",0,0),("a",1,1),("a",1,1),("b",0,0),("b",1,1),("b",1,1),("b",0,0)]
  for i,(st,x,y) in enumerate(vals): rows.append(PairObservation(s,"L","R",str(i),bool(x),bool(y),st,now))
  p=conditional_profile(rows)
  self.assertEqual(len(p.stratum_phi),2)
  self.assertGreater(p.pooled_phi,0)
