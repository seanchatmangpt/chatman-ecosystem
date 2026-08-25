import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.state import Observation
from scripts.measure_train.federation_convergence_realization_msa.oscillation import signature
class T(unittest.TestCase):
 def test_recurrence(self):
  now=datetime.now(timezone.utc); states=['CONVERGING','STALLED','CONVERGING']; rows=[]
  for i,st in enumerate(states): rows.append(Observation(Subject('o/r',chr(97+i)*40,'d'*64,i+1),str(i),st,1,Fraction(1),Fraction(0),now+timedelta(seconds=i)))
  self.assertTrue(signature(rows)['oscillating'])
