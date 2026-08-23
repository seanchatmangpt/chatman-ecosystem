import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.subject import Subject
from scripts.measure_train.transport_invariance_realization_msa.stress import StressIdentity
from scripts.measure_train.transport_invariance_realization_msa.case import RealizationCase
from scripts.measure_train.transport_invariance_realization_msa.frontier import StressCalibrationModel
from scripts.measure_train.transport_invariance_realization_msa.methodology import REQUIRED,require_methods
from scripts.measure_train.transport_invariance_realization_msa.qualify import qualify
from scripts.measure_train.transport_invariance_realization_msa.replay import replay
from scripts.measure_train.transport_invariance_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_full_methodology_and_receipt_tamper(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); rows=[]
  for i,m in enumerate(sorted(REQUIRED)):
   rows.append(RealizationCase(s,StressIdentity(f"s{i}","CALIBRATION_DRIFT",Fraction(i,20),3),False,Fraction(1,10),False,Fraction(1,5),m,"BEAM" if i%2==0 else "PLAN","us-a" if i%2==0 else "eu-b",f"r{i%3}",f"c{i}",now))
  self.assertEqual(set(require_methods(rows)),REQUIRED)
  q=qualify(s,rows,[StressCalibrationModel(3,"d"*64,20,0.1,0.2,"CALIBRATED")],now); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  q["receipt"]["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(q["receipt"])
