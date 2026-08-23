import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.subject import Subject
from scripts.measure_train.transport_invariance_realization_msa.stress import StressIdentity
from scripts.measure_train.transport_invariance_realization_msa.case import RealizationCase
from scripts.measure_train.transport_invariance_realization_msa.frontier import StressCalibrationModel
from scripts.measure_train.transport_invariance_realization_msa.methodology import REQUIRED
from scripts.measure_train.transport_invariance_realization_msa.qualify import qualify
from scripts.measure_train.transport_invariance_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_clean_realization_caps_at_partial_and_red_dependency_dominates(self):
  now=datetime.now(timezone.utc); s=Subject("seanchatmangpt/chatman-ecosystem","7"*40,"8"*64); rows=[]
  for i,m in enumerate(sorted(REQUIRED)):
   rows.append(RealizationCase(s,StressIdentity(f"stress-{i}","TARGET_SHIFT",Fraction(i,20),5),False,Fraction(1,5),False,Fraction(1,4),m,"BEAM" if i%2==0 else "PLAN","us-west" if i%2==0 else "eu-west",f"root-{i%3}",f"case-{i}",now))
  model=StressCalibrationModel(5,"9"*64,50,0.05,0.2,"CALIBRATED")
  q=qualify(s,rows,[model],now); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  broken=qualify(s,rows,[model],now,dependency_states=["BUILD_BROKEN"]); self.assertEqual(broken["standing"],"BUILD_BROKEN"); self.assertIsNone(broken["receipt"])
