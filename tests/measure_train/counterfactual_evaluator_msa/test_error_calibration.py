import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.case import EvaluationCase
from scripts.measure_train.counterfactual_evaluator_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_reliable_and_sparse(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); e=EstimatorIdentity("ips","IPS","1"*64)
  cs=[EvaluationCase(s,e,str(i),Fraction(1,2),Fraction(1,2)+Fraction(i-1,20),Fraction(1,2),Fraction(1,2),now) for i in range(3)]
  self.assertEqual(calibrate("ips",cs).state,"CALIBRATED"); self.assertEqual(calibrate("ips",cs[:2]).state,"INSUFFICIENT")
