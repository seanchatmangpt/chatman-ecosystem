from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.federation_epistemic_capital_control import *
METHODS=sorted(REQUIRED)
def evidence():
    now=datetime.now(timezone.utc)-timedelta(minutes=2); out=[]
    for i,m in enumerate(METHODS): out.append(TransportEvidence(f"e{i}",9,f"t{i}",f"impl{i}",f"model{i}",f"domain{i}",f"cause{i}",False,True,True,1.0,.1,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root{i}",now+timedelta(seconds=i)))
    return out
def geom(xs): return CorrelationGeometry([x.transport_id for x in xs],[])
import unittest
class T(unittest.TestCase):
 def test_calibration_info(self):
  xs=evidence(); g=geom(xs); c=capital(xs,generalized_ess(g),partition(g)); cal=calibrate(xs,9,c); self.assertTrue(cal.admitted); self.assertEqual(current([cal]).generation,9); self.assertEqual(score(xs,g).effective_gain,score(xs,g).nominal_gain)
 def test_split(self):
  a=Calibration(10,'a'*64,10,Fraction(5),Fraction(0),Fraction(0),Fraction(0)); b=Calibration(10,'b'*64,10,Fraction(5),Fraction(0),Fraction(0),Fraction(0))
  with self.assertRaises(Refused): current([a,b])
