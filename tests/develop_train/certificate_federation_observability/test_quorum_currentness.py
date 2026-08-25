import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.certificate_federation_observability import *
C=Certificate(7,"c"*64,"d"*64,"e"*64,"f"*64); NOW=datetime.now(timezone.utc); T1=Transport("gh-api","impl-a","model-a","domain-a"); T2=Transport("git-ref","impl-b","model-b","domain-b")
def resolved(i,t,rel=Relation.EXACT): return Observation(f"o{i}",t.transport_id,7,TransportState.RESOLVED,rel,"a"*40,"b"*64,C.digest,NOW-timedelta(seconds=1),10+i)
class T(unittest.TestCase):
 def test_quorum(self):
  obs=[resolved(1,T1),resolved(2,T2,Relation.ADVANCED)]; self.assertEqual(exact_quorum(obs).votes,2); self.assertEqual(require_current(currentness(obs,60,NOW),2).current,2)
 def test_split(self):
  x=resolved(2,T2); x=Observation(x.observation_id,x.transport_id,x.certificate_generation,x.state,x.relation,x.observed_sha,x.semantic_digest,"0"*64,x.observed_at,x.latency_ms)
  with self.assertRaises(Refused): exact_quorum([resolved(1,T1),x])
