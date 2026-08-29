from datetime import datetime,timezone,timedelta
from scripts.develop_train.federation_epistemic_capital_control import *
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
METHODS=sorted(REQUIRED)
def evidence():
    now=datetime.now(timezone.utc)-timedelta(minutes=2); out=[]
    for i,m in enumerate(METHODS): out.append(TransportEvidence(f"e{i}",9,f"t{i}",f"impl{i}",f"model{i}",f"domain{i}",f"cause{i}",False,True,True,1.0,.1,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root{i}",now+timedelta(seconds=i)))
    return out
def geom(xs): return CorrelationGeometry([x.transport_id for x in xs],[])
import unittest
class T(unittest.TestCase):
 def test_chicago(self):
  xs=evidence(); q=qualify(SUB,9,xs,geom(xs),3,list(FailureWorld))
  self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertEqual(q.effective_capital,len(xs)); self.assertEqual(replay(q.receipt,q.receipt.digest),'REPLAY_MATCH')
  red=qualify(SUB,9,xs,geom(xs),3,list(FailureWorld),{'root':['dep'],'dep':[]},{'dep':'BUILD_BROKEN'})
  self.assertEqual(red.standing,'BUILD_BROKEN'); self.assertIsNone(red.receipt)
