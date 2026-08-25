import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.subject import Subject
from scripts.measure_train.transport_invariance_realization_msa.stress import StressIdentity
from scripts.measure_train.transport_invariance_realization_msa.case import RealizationCase
from scripts.measure_train.transport_invariance_realization_msa.trajectory import trajectory,risk_monotonicity,local_sensitivity,estimate_threshold
from scripts.measure_train.transport_invariance_realization_msa.regret import ObservedAlternative,observed_regret
from scripts.measure_train.transport_invariance_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_trajectory_monotonicity_sensitivity_threshold_and_regret(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); rows=[]
  for i,(mag,risk,ok) in enumerate([(Fraction(0),Fraction(1,10),True),(Fraction(1,4),Fraction(1,5),True),(Fraction(1,2),Fraction(3,5),False)]):
   rows.append(RealizationCase(s,StressIdentity(f"s{i}","SUPPORT_EROSION",mag,1),mag<Fraction(1,2),risk,ok,risk,"SIMULATION","WASM","us-a","r",f"c{i}",now))
  pts=trajectory(rows); self.assertEqual(risk_monotonicity(pts).violations,0); self.assertGreater(local_sensitivity(pts).max_slope,Fraction(0)); self.assertEqual(estimate_threshold(pts).first_failure,Fraction(1,2))
  chosen=rows[1]; self.assertEqual(observed_regret(chosen,[ObservedAlternative(chosen.case_id,"ALT",Fraction(1,10))]),Fraction(1,10))
  with self.assertRaises(Refused): observed_regret(chosen,[])
