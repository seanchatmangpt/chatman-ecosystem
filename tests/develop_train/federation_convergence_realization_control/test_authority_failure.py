from datetime import datetime,timezone,timedelta
import unittest
from scripts.develop_train.federation_convergence_realization_control.api import *
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=2); out=[]; n=len(METHODS)
    for i,m in enumerate(METHODS):
        b=n-2-i if i<n-2 else 0
        out.append(ConvergenceObservation(f"o{i}",i,"b"*64,i>=n-2,b,0,0,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i%3}",now+timedelta(seconds=i)))
    return out
class T(unittest.TestCase):
    def test_authority_failure_replay(self):
        with self.assertRaises(Refused): admit(Action.DO)
        self.assertEqual(admit(Action.DO,"BRCE"),Action.DO); self.assertEqual(len(require_complete(list(FailureWorld))),7)
        q=qualify(Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40),observations()); self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
    def test_cycle(self):
        with self.assertRaises(Refused): blockers({"a":["b"],"b":["a"]},{})
if __name__=="__main__": unittest.main()
