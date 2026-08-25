import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.state import Observation
from scripts.measure_train.federation_convergence_realization_msa.capital import Source
from scripts.measure_train.federation_convergence_realization_msa.methodology import REQUIRED
from scripts.measure_train.federation_convergence_realization_msa.qualify import qualify
from scripts.measure_train.federation_convergence_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_ceiling_and_red_dependency(self):
  now=datetime.now(timezone.utc); rows=[]
  for i in range(5):
   st='FIXED' if i==4 else 'CONVERGING'; s=Subject('o/r',chr(97+i)*40,'d'*64,i+1); rows.append(Observation(s,str(i),st,max(0,4-i),Fraction(max(0,4-i),4),Fraction(0),now+timedelta(seconds=i),predicted_fixed=(st=='FIXED')))
  src=[Source('a','1'*64,'2'*64,'c1'),Source('b','3'*64,'4'*64,'c2')]
  q=qualify(rows[-1].subject,rows,src,REQUIRED,now+timedelta(seconds=10)); self.assertEqual(q['standing'],'PARTIAL_ALIVE'); self.assertEqual(replay(q['receipt']),'REPLAY_MATCH')
  r=qualify(rows[-1].subject,rows,src,REQUIRED,now+timedelta(seconds=10),dependencies=('BUILD_BROKEN',)); self.assertEqual(r['standing'],'BUILD_BROKEN'); self.assertIsNone(r['receipt'])
