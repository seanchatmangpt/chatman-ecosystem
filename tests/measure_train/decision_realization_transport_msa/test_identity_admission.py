import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.decision_realization_transport_msa.subject import Subject
from scripts.measure_train.decision_realization_transport_msa.stratum import Stratum
from scripts.measure_train.decision_realization_transport_msa.observation import Observation
from scripts.measure_train.decision_realization_transport_msa.admission import admit
from scripts.measure_train.decision_realization_transport_msa.errors import Refused
class T(unittest.TestCase):
 def test_exact_and_unobserved(self):
  s=Subject("o/r","a"*40,"b"*64); st=Stratum("DISCOVERY","BEAM","us","r")
  o=Observation(s,"x",st,Fraction(1,5),Fraction(1,4),False,datetime.now(timezone.utc))
  with self.assertRaises(Refused): admit(s,[o],datetime.now(timezone.utc))
