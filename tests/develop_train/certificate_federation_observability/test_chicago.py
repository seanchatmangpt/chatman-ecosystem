import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.certificate_federation_observability import *
S=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
C=Certificate(7,"c"*64,"d"*64,"e"*64,"f"*64); NOW=datetime.now(timezone.utc)
T1=Transport("gh-api","impl-a","model-a","domain-a"); T2=Transport("git-ref","impl-b","model-b","domain-b")
def resolved(i,t): return Observation(f"o{i}",t.transport_id,7,TransportState.RESOLVED,Relation.EXACT,"a"*40,"b"*64,C.digest,NOW-timedelta(seconds=1),10+i)
class T(unittest.TestCase):
 def test_chicago(self):
  obs=[resolved(1,T1),resolved(2,T2)]; q=qualify(S,C,obs); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
  with self.assertRaises(Refused): admit(Action.DO)
  self.assertEqual(admit(Action.DO,"BRCE"),Action.DO)
  red=qualify(S,C,obs,("BUILD_BROKEN",)); self.assertEqual(red.standing,"BUILD_BROKEN"); self.assertIsNone(red.receipt)
 def test_cycle(self):
  with self.assertRaises(Refused): blockers({"a":("b",),"b":("a",)},{})
