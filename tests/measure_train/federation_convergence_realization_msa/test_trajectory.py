import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.state import Observation
from scripts.measure_train.federation_convergence_realization_msa.trajectory import admit
from scripts.measure_train.federation_convergence_realization_msa.refusals import Refused
class T(unittest.TestCase):
 def test_torn_refuses(self):
  now=datetime.now(timezone.utc); a=Subject('o/r','a'*40,'d'*64,1); c=Subject('o/r','c'*40,'d'*64,3)
  rows=[Observation(a,'1','CONVERGING',1,Fraction(1),Fraction(0),now),Observation(c,'2','FIXED',0,Fraction(0),Fraction(0),now+timedelta(seconds=1))]
  with self.assertRaisesRegex(Refused,'TORN_GENERATION'): admit(c,rows,now+timedelta(seconds=2))
