import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.case import EvaluationCase
from scripts.measure_train.counterfactual_evaluator_msa.weights import weight_diagnostics
class T(unittest.TestCase):
 def test_ess(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); e=EstimatorIdentity("ips","IPS","1"*64)
  cs=[EvaluationCase(s,e,str(i),Fraction(1,2),Fraction(1,2),Fraction(1,2),Fraction(1,2),now) for i in range(3)]
  d=weight_diagnostics(cs); self.assertEqual(d.ess,Fraction(3)); self.assertEqual(d.max_to_mean,Fraction(1))
