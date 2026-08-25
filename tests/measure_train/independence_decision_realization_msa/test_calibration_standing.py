import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.independence_decision_realization_msa.subject import Subject
from scripts.measure_train.independence_decision_realization_msa.policy import DecisionPolicy
from scripts.measure_train.independence_decision_realization_msa.observation import DecisionObservation
from scripts.measure_train.independence_decision_realization_msa.calibration import calibrate
from scripts.measure_train.independence_decision_realization_msa.drift import cusum_loss
from scripts.measure_train.independence_decision_realization_msa.frontier import PolicyModel,current_frontier
from scripts.measure_train.independence_decision_realization_msa.census import census
from scripts.measure_train.independence_decision_realization_msa.strata import stratify
from scripts.measure_train.independence_decision_realization_msa.standing import standing
from scripts.measure_train.independence_decision_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_calibration_currentness_strata_and_failure_dominance(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); p=DecisionPolicy("p",2,"c"*64,Fraction(10),Fraction(1),Fraction(1))
  rows=[DecisionObservation(s,"p",2,"c"*64,str(i),"INDEPENDENT","INDEPENDENT",Fraction(9,10),now,"risk","MONITORING","BEAM","us-west" if i<4 else "us-east","root") for i in range(8)]
  self.assertEqual(calibrate(rows).state,"CALIBRATED"); self.assertTrue(cusum_loss([Fraction(5),Fraction(5)],Fraction(1),Fraction(0),Fraction(4)).drifted)
  self.assertEqual(current_frontier([PolicyModel("p",1,"a"*64,"CALIBRATED"),PolicyModel("p",2,"b"*64,"CALIBRATED")])[0].generation,2)
  with self.assertRaises(Refused): current_frontier([PolicyModel("p",2,"a"*64,"CALIBRATED"),PolicyModel("p",2,"b"*64,"CALIBRATED")])
  c=census(p,rows); self.assertEqual(set(stratify(p,rows,"region")),{"us-east","us-west"}); self.assertEqual(standing(c),"PARTIAL_ALIVE"); self.assertEqual(standing(c,dependency_states=["BUILD_BROKEN"]),"BUILD_BROKEN")
