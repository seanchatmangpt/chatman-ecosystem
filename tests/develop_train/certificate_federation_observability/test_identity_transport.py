import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.certificate_federation_observability import *
S=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
C=Certificate(7,"c"*64,"d"*64,"e"*64,"f"*64)
NOW=datetime.now(timezone.utc)
T1=Transport("gh-api","impl-a","model-a","domain-a")
T2=Transport("git-ref","impl-b","model-b","domain-b")
def resolved(i,t,rel=Relation.EXACT,age=1): return Observation(f"o{i}",t.transport_id,7,TransportState.RESOLVED,rel,"a"*40,"b"*64,C.digest,NOW-timedelta(seconds=age),10+i)
class T(unittest.TestCase):
 def test_exact(self):
  with self.assertRaises(Refused): Subject.parse("x/y@abc")
  self.assertEqual(len(witness([T1,T2]).transports),2)
 def test_alias(self):
  with self.assertRaises(Refused): witness([T1,Transport("x","ix","model-a","dx")])
