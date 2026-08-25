import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.subject import Subject
from scripts.measure_train.distributional_robustness_realization_msa.distribution import Distribution
from scripts.measure_train.distributional_robustness_realization_msa.ambiguity import AmbiguityModel
from scripts.measure_train.distributional_robustness_realization_msa.observation import RealizationObservation
from scripts.measure_train.distributional_robustness_realization_msa.methodology import REQUIRED
from scripts.measure_train.distributional_robustness_realization_msa.qualify import qualify
from scripts.measure_train.distributional_robustness_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_full_method_bounded_red_dependency_dominates(self):
  now=datetime.now(timezone.utc); s=Subject("seanchatmangpt/process","a"*40,"b"*64,7); d=Distribution((("ok",Fraction(1)),)); m=AmbiguityModel("TV",Fraction(1,10),3,"c"*64); rows=[]
  for i,method in enumerate(sorted(REQUIRED)): rows.append(RealizationObservation(s,f"e{i}",m,d,Fraction(1,10),Fraction(1,5),Fraction(1,5),method,f"engine{i%2}",f"region{i%2}",f"root{i%3}",now))
  q=qualify(s,rows,[m],now,lambda r:r.realized_loss<=r.predicted_worst_loss); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  red=qualify(s,rows,[m],now,lambda r:True,dependencies=("BUILD_BROKEN",)); self.assertEqual(red["standing"],"BUILD_BROKEN"); self.assertIsNone(red["receipt"])
