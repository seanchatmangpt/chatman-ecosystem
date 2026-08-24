import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.state import Observation
from scripts.measure_train.federation_convergence_realization_msa.potential import descent_fraction
from scripts.measure_train.federation_convergence_realization_msa.oscillation import signature
from scripts.measure_train.federation_convergence_realization_msa.hitting import seconds
class T(unittest.TestCase):
 def test_descent(self):
  now=datetime.now(timezone.utc); rows=[]
  for i,(st,b,e) in enumerate([('CONVERGING',2,2),('CONVERGING',1,1),('FIXED',0,0)]):
   s=Subject('o/r',chr(97+i)*40,'d'*64,i+1); rows.append(Observation(s,str(i),st,b,Fraction(e),Fraction(0),now+timedelta(seconds=i),predicted_fixed=(st=='FIXED')))
  self.assertEqual(descent_fraction(rows),Fraction(1)); self.assertFalse(signature(rows)['oscillating']); self.assertEqual(seconds(rows),2)
