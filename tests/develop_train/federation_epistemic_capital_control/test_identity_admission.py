from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.federation_epistemic_capital_control import *
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
METHODS=sorted(REQUIRED)
def evidence():
    now=datetime.now(timezone.utc)-timedelta(minutes=2); out=[]
    for i,m in enumerate(METHODS): out.append(TransportEvidence(f"e{i}",9,f"t{i}",f"impl{i}",f"model{i}",f"domain{i}",f"cause{i}",False,True,True,1.0,.1,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root{i}",now+timedelta(seconds=i)))
    return out
import unittest
class T(unittest.TestCase):
 def test_identity_admission(self):
  with self.assertRaises(Refused): Subject.parse('bad')
  xs=evidence(); self.assertEqual(len(admit_evidence(xs,9)),len(METHODS))
  with self.assertRaises(Refused): admit_evidence(xs+[xs[0]],9)
