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
 def test_ess(self):
  xs=evidence(); e=generalized_ess(geom(xs)); self.assertEqual(e.generalized,len(xs)); self.assertEqual(capital(xs,e,partition(geom(xs))).effective,len(xs))
 def test_pseudo_quorum(self):
  xs=evidence()[:3]; es=[CorrelationEdge(xs[0].transport_id,xs[1].transport_id,Fraction(9,10),common_cause=True),CorrelationEdge(xs[1].transport_id,xs[2].transport_id,Fraction(9,10),common_cause=True),CorrelationEdge(xs[0].transport_id,xs[2].transport_id,Fraction(9,10),common_cause=True)]; g=CorrelationGeometry([x.transport_id for x in xs],es); c=capital(xs,generalized_ess(g),partition(g)); self.assertEqual(c.cause_units,1)
  with self.assertRaises(Refused): evaluate_quorum(c,3)
