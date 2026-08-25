from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.certificate_federation_realization_control import *
from scripts.develop_train.certificate_federation_realization_control.observation import Observation
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
CERT=Certificate(7,"b"*64,"c"*64)
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=1)
    return [Observation(f"o{i}",7,f"t{i%3}",f"impl{i%3}",f"model{i%3}",f"domain{i%3}",TransportState.RESOLVED,True,True,Relation.EXACT,10+i,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i}",now+timedelta(seconds=i)) for i,m in enumerate(METHODS)]
class Chicago(unittest.TestCase):
    def test_full_realization_and_failure_dominance(self):
        obs=observations(); q=qualify(SUB,CERT,obs)
        self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertIsNotNone(q.receipt); self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
        red=qualify(SUB,CERT,obs,graph={"root":["dep"],"dep":[]},standings={"dep":"BUILD_BROKEN"})
        self.assertEqual(red.standing,"BUILD_BROKEN"); self.assertIsNone(red.receipt)
if __name__=="__main__": unittest.main()
