import unittest
from fractions import Fraction
from scripts.measure_train.validation_independence_realization_msa.subject import Subject
from scripts.measure_train.validation_independence_realization_msa.graph import Evidence
from scripts.measure_train.validation_independence_realization_msa.validator import Validator
from scripts.measure_train.validation_independence_realization_msa.empirical import PairStats
from scripts.measure_train.validation_independence_realization_msa.calibration import Calibration
from scripts.measure_train.validation_independence_realization_msa.frontier import IndependenceModel
from scripts.measure_train.validation_independence_realization_msa.robustness import Robustness
from scripts.measure_train.validation_independence_realization_msa.qualify import qualify
from scripts.measure_train.validation_independence_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_clean_independence_evidence_caps_at_partial_alive(self):
  s=Subject("o/r","a"*40,"b"*64)
  ev=[Evidence("x",(),1,"c"*64),Evidence("y",(),1,"d"*64)]
  va=Validator("a","1"*64,"2"*64,"3"*64,"left","x"); vb=Validator("b","4"*64,"5"*64,"6"*64,"right","y")
  cal=Calibration(20,Fraction(0),Fraction(0),Fraction(1),"CALIBRATED")
  q=qualify(s,ev,[va,vb],PairStats(20,0.25,0.0,0.0),cal,[IndependenceModel(4,"7"*64,"CALIBRATED")],Robustness(Fraction(0),Fraction(0),Fraction(0)))
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
