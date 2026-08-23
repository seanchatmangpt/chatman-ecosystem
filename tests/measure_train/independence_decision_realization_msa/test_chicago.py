import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.independence_decision_realization_msa.subject import Subject
from scripts.measure_train.independence_decision_realization_msa.policy import DecisionPolicy
from scripts.measure_train.independence_decision_realization_msa.observation import DecisionObservation
from scripts.measure_train.independence_decision_realization_msa.regret import ObservedAlternative
from scripts.measure_train.independence_decision_realization_msa.voi import DeferRealization
from scripts.measure_train.independence_decision_realization_msa.qualify import qualify
from scripts.measure_train.independence_decision_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_clean_realization_caps_at_partial_alive_and_red_dependency_dominates(self):
  now=datetime.now(timezone.utc); s=Subject("seanchatmangpt/chatman-ecosystem","a"*40,"b"*64); p=DecisionPolicy("risk-independence",7,"c"*64,Fraction(10),Fraction(1),Fraction(1))
  rows=[]
  for i in range(10):
   truth="INDEPENDENT" if i<8 else "DEPENDENT"; prob=Fraction(9,10) if truth=="INDEPENDENT" else Fraction(1,10)
   rows.append(DecisionObservation(s,p.policy_id,p.generation,p.digest,str(i),truth,truth,prob,now,"MIN_EXPECTED_LOSS","CONFORMANCE","BEAM","us-west","root-a"))
  alt=[ObservedAlternative(str(i),rows[i].decision,Fraction(0),True) for i in range(10)]
  q=qualify(s,p,rows,now+timedelta(seconds=1),alternatives=alt,defer_realizations=[DeferRealization("d",Fraction(3),Fraction(1),Fraction(1),Fraction(0),True)])
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  self.assertEqual(qualify(s,p,rows,now+timedelta(seconds=1),dependency_states=["BUILD_BROKEN"])["standing"],"BUILD_BROKEN")
