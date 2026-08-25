import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.federation_epistemic_capital_msa.subject import Subject
from scripts.measure_train.federation_epistemic_capital_msa.transport import Transport
from scripts.measure_train.federation_epistemic_capital_msa.observation import TrialObservation
from scripts.measure_train.federation_epistemic_capital_msa.admission import admit
from scripts.measure_train.federation_epistemic_capital_msa.refusal import Refused
class T(unittest.TestCase):
 def test_future_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); t=Transport("t","c"*64,"d"*64,"api",1); r=TrialObservation(s,t,"1",False,True,True,now+timedelta(seconds=1),"DISCOVERY","e","r","root")
  with self.assertRaises(Refused): admit(s,[r],now)
