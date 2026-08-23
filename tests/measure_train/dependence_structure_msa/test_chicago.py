import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.dependence_structure_msa.subject import Subject
from scripts.measure_train.dependence_structure_msa.observation import PairObservation
from scripts.measure_train.dependence_structure_msa.calibration import Calibration
from scripts.measure_train.dependence_structure_msa.frontier import DependenceModel
from scripts.measure_train.dependence_structure_msa.provenance import ProvenanceClaim
from scripts.measure_train.dependence_structure_msa.qualify import qualify_pair
from scripts.measure_train.dependence_structure_msa.replay import replay
class T(unittest.TestCase):
 def test_independence_must_be_empirical_and_failure_dominates(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  pattern=[(0,0),(0,1),(1,0),(1,1)]*3
  rows=[PairObservation(s,"L","R",str(i),bool(x),bool(y),"all",now) for i,(x,y) in enumerate(pattern)]
  cal=Calibration(12,Fraction(0),Fraction(0),"CALIBRATED")
  model=DependenceModel("L|R",1,"c"*64,"CALIBRATED")
  claim=ProvenanceClaim("L","R",True,True,True,True)
  q=qualify_pair(s,rows,now,cal,model,claim)
  self.assertEqual(q["verdict"],"INDEPENDENT")
  self.assertEqual(q["mode"],"INDEPENDENT")
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  self.assertFalse(q["actuation_performed"])
  q2=qualify_pair(s,rows,now,cal,model,claim,dependency_states=("BUILD_BROKEN",))
  self.assertEqual(q2["standing"],"BUILD_BROKEN")
