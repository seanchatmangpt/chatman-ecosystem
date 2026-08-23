import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.case import EvaluationCase
from scripts.measure_train.counterfactual_evaluator_msa.admission import admit_cases
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_duplicate_future(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); e=EstimatorIdentity("ips","IPS","1"*64)
  c=EvaluationCase(s,e,"x",Fraction(1,2),Fraction(1,2),Fraction(1,2),Fraction(1,2),now)
  with self.assertRaises(Refused): admit_cases(s,[c,c],now)
  f=EvaluationCase(s,e,"y",Fraction(1,2),Fraction(1,2),Fraction(1,2),Fraction(1,2),now+timedelta(seconds=1))
  with self.assertRaises(Refused): admit_cases(s,[f],now)
