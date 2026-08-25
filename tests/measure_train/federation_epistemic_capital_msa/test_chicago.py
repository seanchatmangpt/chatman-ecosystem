import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.federation_epistemic_capital_msa.subject import Subject
from scripts.measure_train.federation_epistemic_capital_msa.transport import Transport
from scripts.measure_train.federation_epistemic_capital_msa.observation import TrialObservation
from scripts.measure_train.federation_epistemic_capital_msa.calibration import Calibration
from scripts.measure_train.federation_epistemic_capital_msa.methodology import REQUIRED
from scripts.measure_train.federation_epistemic_capital_msa.qualify import qualify
from scripts.measure_train.federation_epistemic_capital_msa.replay import replay
class T(unittest.TestCase):
 def test_bounded_positive_and_red_dependency(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); rows=[]; methods=sorted(REQUIRED); patterns={"x":[0,0,1,0,1,1,0,1,0,1,0],"y":[0,1,0,1,1,0,1,0,1,0,1],"z":[1,0,0,1,0,1,1,0,0,1,1]}
  for ti,(tid,vals) in enumerate(patterns.items()):
   t=Transport(tid,(tid*64)[:64],((tid+"m")*64)[:64],"domain-"+tid,1)
   for i,v in enumerate(vals): rows.append(TrialObservation(s,t,str(i),bool(v),False,False,now+timedelta(seconds=i+20*ti),methods[i],"engine-"+tid,"region-"+tid,"root-"+tid))
  c=Calibration(20,Fraction(0),Fraction(0),Fraction(0),"CALIBRATED"); q=qualify(s,rows,c); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH"); self.assertFalse(q["actuation_performed"]); red=qualify(s,rows,c,["BUILD_BROKEN"]); self.assertEqual(red["standing"],"BUILD_BROKEN"); self.assertIsNone(red["receipt"])
