import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.independence_decision_realization_msa.subject import Subject
from scripts.measure_train.independence_decision_realization_msa.policy import DecisionPolicy
from scripts.measure_train.independence_decision_realization_msa.observation import DecisionObservation
from scripts.measure_train.independence_decision_realization_msa.loss import realized_loss
from scripts.measure_train.independence_decision_realization_msa.selective_risk import selective_risk
from scripts.measure_train.independence_decision_realization_msa.regret import ObservedAlternative,observed_regret
from scripts.measure_train.independence_decision_realization_msa.voi import DeferRealization,realized_voi
from scripts.measure_train.independence_decision_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_realized_economics(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); p=DecisionPolicy("p",1,"c"*64,Fraction(10),Fraction(1),Fraction(2))
  row=DecisionObservation(s,"p",1,"c"*64,"1","INDEPENDENT","DEPENDENT",Fraction(3,4),now,"risk","DISCOVERY","BEAM","r","root")
  self.assertEqual(realized_loss(p,[row]).mean_loss,10); self.assertEqual(selective_risk([row]).conditional_error,1)
  self.assertEqual(observed_regret(p,[row],[ObservedAlternative("1","DEPENDENT",Fraction(0),True)])["mean_regret"],10)
  with self.assertRaises(Refused): observed_regret(p,[row],[ObservedAlternative("1","DEPENDENT",Fraction(0),False)])
  self.assertEqual(realized_voi([DeferRealization("d",Fraction(5),Fraction(1),Fraction(1),Fraction(1),True)])["mean_value"],2)
