import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.acquisition_realization.subject import Subject
from scripts.measure_train.acquisition_realization.plan import AcquisitionPlan
from scripts.measure_train.acquisition_realization.outcome import AcquisitionOutcome
from scripts.measure_train.acquisition_realization.proper_score import brier_score
from scripts.measure_train.acquisition_realization.efficiency import evaluate
class T(unittest.TestCase):
 def test_scores_and_resource_slip(self):
  s=Subject("o/r","a"*40); p=AcquisitionPlan(s,"p",1,"MAX_INFORMATION_PER_COST","c",Fraction(1,4),Fraction(3,4),Fraction(2),100,"1"*64)
  o=AcquisitionOutcome(s,"p","c",datetime.now(timezone.utc),"PASS",Fraction(1,10),Fraction(3),150,"e")
  self.assertEqual(brier_score(p.predicted_pass,"PASS"),Fraction(1,16))
  eff=evaluate(p,o,0.2); self.assertEqual(eff.cost_ratio,Fraction(3,2)); self.assertEqual(eff.latency_ratio,Fraction(3,2))
