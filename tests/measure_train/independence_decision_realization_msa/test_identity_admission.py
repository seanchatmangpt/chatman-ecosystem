import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.independence_decision_realization_msa.subject import Subject
from scripts.measure_train.independence_decision_realization_msa.policy import DecisionPolicy
from scripts.measure_train.independence_decision_realization_msa.observation import DecisionObservation
from scripts.measure_train.independence_decision_realization_msa.admission import admit
from scripts.measure_train.independence_decision_realization_msa.confusion import confusion
from scripts.measure_train.independence_decision_realization_msa.errors import Refused
class T(unittest.TestCase):
 def row(self,s,p,i,d,t,now): return DecisionObservation(s,p.policy_id,p.generation,p.digest,i,d,t,Fraction(3,4),now,"risk","DISCOVERY","BEAM","us-west","root")
 def test_identity_asymmetric_policy_and_admission(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); p=DecisionPolicy("p",1,"c"*64,Fraction(10),Fraction(1),Fraction(2))
  self.assertEqual(p.realized_loss("INDEPENDENT","DEPENDENT"),10)
  rows=[self.row(s,p,"1","INDEPENDENT","INDEPENDENT",now),self.row(s,p,"2","INDEPENDENT","DEPENDENT",now),self.row(s,p,"3","DEFER","DEPENDENT",now)]
  c=confusion(admit(s,p,rows,now+timedelta(seconds=1)))
  self.assertEqual((c.correct,c.false_independent,c.deferred),(1,1,1))
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
  with self.assertRaises(Refused): admit(s,p,[self.row(s,p,"x","DEPENDENT","DEPENDENT",now+timedelta(seconds=5))],now)
