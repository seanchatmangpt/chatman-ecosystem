import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.state import Observation
from scripts.measure_train.federation_convergence_realization_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_calibrated(self):
  now=datetime.now(timezone.utc); rows=[]
  for i in range(5):
   st='FIXED' if i==4 else 'CONVERGING'; s=Subject('o/r',chr(97+i)*40,'d'*64,i+1); rows.append(Observation(s,str(i),st,0,Fraction(0),Fraction(0),now+timedelta(seconds=i),predicted_fixed=(st=='FIXED')))
  self.assertEqual(calibrate(rows).state,'CALIBRATED')
