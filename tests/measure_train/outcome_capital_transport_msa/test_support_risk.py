import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.outcome_capital_transport_msa.subject import Subject
from scripts.measure_train.outcome_capital_transport_msa.observation import OutcomeObservation
from scripts.measure_train.outcome_capital_transport_msa.support import profile,require_support
from scripts.measure_train.outcome_capital_transport_msa.loss import LossMatrix
from scripts.measure_train.outcome_capital_transport_msa.risk import horvitz_thompson,self_normalized
class T(unittest.TestCase):
 def test_selective_support_and_risk(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[OutcomeObservation(s,str(i),"DISCOVERY","e","r","root",1,Fraction(1,2),Fraction(0),"INDEPENDENT","INDEPENDENT",now) for i in range(5)]
  p=profile(rows); self.assertTrue(require_support(p,min_ess=Fraction(5)))
  m=LossMatrix(Fraction(1),Fraction(1),Fraction(1,4))
  self.assertEqual(horvitz_thompson(rows,m),0); self.assertEqual(self_normalized(rows,m),0)
